import { createHash } from "node:crypto";
import { eq } from "drizzle-orm";
import { beforeAll, describe, expect, test } from "vitest";
import { seedDirectory } from "#test/fixtures/directory.js";
import { CONSENT_NOTICE } from "#lib/domain/consent-notice.js";
import { leadFormSchema, type LeadFormInput } from "#lib/domain/lead-form.js";
import { db } from "../db/index.js";
import { auditLogs, consentRecords, patientLeads } from "../db/schema/index.js";
import { createLead } from "./create-lead.js";

const request = { ipAddress: "203.0.113.9", userAgent: "LeadTest/1.0" };
let slug: (name: string) => string;

beforeAll(async () => {
  ({ slug } = await seedDirectory("cl"));
});

const submit = (input: Partial<LeadFormInput>) =>
  createLead(
    leadFormSchema.parse({
      fullName: "Chidi Okafor",
      email: "chidi@example.com",
      phone: "+234 801 234 5678",
      countryCode: "NG",
      intent: "treatment",
      description: "Needs CABG, cardiologist in Lagos referred.",
      consent: true,
      ...input
    }),
    request
  );

describe("createLead", () => {
  test("saves the lead, its consent record and audit rows together", async () => {
    const lead = await submit({ sourcePath: "/treatments/cabg", utm: { source: "google" } });
    expect(lead.refNo).toBeGreaterThanOrEqual(1001);

    const [saved] = await db.select().from(patientLeads).where(eq(patientLeads.id, lead.id));
    expect(saved).toMatchObject({
      phone: "+2348012345678",
      passportCountry: "NG",
      status: "new",
      utm: { source: "google" }
    });

    const consents = await db
      .select()
      .from(consentRecords)
      .where(eq(consentRecords.leadId, lead.id));
    expect(consents).toHaveLength(1);
    expect(consents[0]).toMatchObject({
      noticeVersion: CONSENT_NOTICE.version,
      noticeSha256: createHash("sha256").update(CONSENT_NOTICE.text).digest("hex"),
      purposes: [
        "case_evaluation",
        "share_with_partner_hospitals",
        "contact_whatsapp_email",
        "cross_border_transfer"
      ],
      ipAddress: "203.0.113.9"
    });

    const audit = await db.select().from(auditLogs).where(eq(auditLogs.leadId, lead.id));
    expect(audit.map((a) => a.action).sort()).toEqual(["consent.granted", "lead.created"]);
    expect(audit.every((a) => a.actorType === "patient" && a.userAgent === "LeadTest/1.0")).toBe(
      true
    );
  });

  test("domestic leads do not consent to cross-border transfer", async () => {
    const lead = await submit({ countryCode: "IN", indianState: "Bihar", phone: "9876543210" });
    const [consent] = await db
      .select()
      .from(consentRecords)
      .where(eq(consentRecords.leadId, lead.id));
    expect(consent?.purposes).not.toContain("cross_border_transfer");
  });

  test("links published page context and ignores unknown or draft slugs", async () => {
    const linked = await submit({
      hospitalSlug: slug("heart-institute"),
      doctorSlug: slug("dr-published")
    });
    const [withContext] = await db
      .select()
      .from(patientLeads)
      .where(eq(patientLeads.id, linked.id));
    expect(withContext?.hospitalId).not.toBeNull();
    expect(withContext?.doctorId).not.toBeNull();

    const ignored = await submit({
      hospitalSlug: slug("draft-hospital"),
      procedureSlug: "no-such-procedure"
    });
    const [withoutContext] = await db
      .select()
      .from(patientLeads)
      .where(eq(patientLeads.id, ignored.id));
    expect(withoutContext).toMatchObject({ hospitalId: null, procedureId: null });
  });

  test("writes nothing if any part of the transaction fails", async () => {
    // An invalid IP makes the consent insert fail after the lead insert succeeded
    await expect(
      createLead(
        leadFormSchema.parse({
          fullName: "Rollback Test",
          email: "rb@example.com",
          phone: "+234 801 234 5678",
          countryCode: "NG",
          intent: "other",
          description: "This lead must be rolled back.",
          consent: true
        }),
        { ipAddress: "not-an-ip", userAgent: null }
      )
    ).rejects.toThrow();
    expect(await db.$count(patientLeads, eq(patientLeads.email, "rb@example.com"))).toBe(0);
  });
});
