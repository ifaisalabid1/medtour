import { createHash } from "node:crypto";
import { and, eq } from "drizzle-orm";
import { CONSENT_NOTICE } from "#lib/domain/consent-notice.js";
import type { LeadForm } from "#lib/domain/lead-form.js";
import { consentPurposesFor } from "#lib/domain/leads.js";
import { recordAudit, type AuditEntry } from "../audit.js";
import { db } from "../db/index.js";
import {
  consentRecords,
  doctors,
  hospitals,
  patientLeads,
  procedures
} from "../db/schema/index.js";

const NOTICE_SHA256 = createHash("sha256").update(CONSENT_NOTICE.text).digest("hex");

type RequestInfo = Pick<AuditEntry, "ipAddress" | "userAgent">;

/** Page-context slugs to ids. Unknown or unpublished slugs become null instead of failing the lead. */
async function resolveContext(form: LeadForm) {
  const [procedure, hospital, doctor] = await Promise.all([
    form.procedureSlug
      ? db
          .select({ id: procedures.id })
          .from(procedures)
          .where(and(eq(procedures.slug, form.procedureSlug), eq(procedures.status, "published")))
      : [],
    form.hospitalSlug
      ? db
          .select({ id: hospitals.id })
          .from(hospitals)
          .where(and(eq(hospitals.slug, form.hospitalSlug), eq(hospitals.status, "published")))
      : [],
    form.doctorSlug
      ? db
          .select({ id: doctors.id })
          .from(doctors)
          .where(and(eq(doctors.slug, form.doctorSlug), eq(doctors.status, "published")))
      : []
  ]);
  return {
    procedureId: procedure[0]?.id ?? null,
    hospitalId: hospital[0]?.id ?? null,
    doctorId: doctor[0]?.id ?? null
  };
}

/**
 * Saves a validated enquiry. The lead, its consent record and both audit rows commit together:
 * a lead without proof of consent can never exist.
 */
export async function createLead(form: LeadForm, request: RequestInfo) {
  const context = await resolveContext(form);
  const purposes = consentPurposesFor(form.countryCode);

  return db.transaction(async (tx) => {
    const [lead] = await tx
      .insert(patientLeads)
      .values({
        fullName: form.fullName,
        email: form.email,
        phone: form.phone,
        description: form.description,
        countryCode: form.countryCode,
        indianState: form.indianState,
        passportCountry: form.passportCountry,
        intent: form.intent,
        reportsStatus: form.reportsStatus,
        travelTimeline: form.travelTimeline,
        needsVisaLetter: form.needsVisaLetter,
        openToPaidTeleconsult: form.openToPaidTeleconsult,
        needsInsuranceHelp: form.needsInsuranceHelp,
        ...context,
        sourcePath: form.sourcePath,
        utm: form.utm ?? {}
      })
      .returning({ id: patientLeads.id, refNo: patientLeads.refNo });
    if (!lead) throw new Error("insert into patient_leads returned no row");

    await tx.insert(consentRecords).values({
      leadId: lead.id,
      noticeVersion: CONSENT_NOTICE.version,
      noticeSha256: NOTICE_SHA256,
      purposes,
      ...request
    });

    const audit = {
      actorType: "patient",
      entityType: "lead",
      entityId: lead.id,
      leadId: lead.id,
      ...request
    } as const;
    await recordAudit({ ...audit, action: "lead.created" }, tx);
    await recordAudit(
      {
        ...audit,
        action: "consent.granted",
        metadata: { noticeVersion: CONSENT_NOTICE.version, purposes }
      },
      tx
    );

    return lead;
  });
}
