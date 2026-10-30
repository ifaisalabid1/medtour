import { LEADS_NOTIFY_EMAIL, SITE_URL } from "$app/env/private";
import { formatLeadRef } from "#lib/domain/leads.js";
import type { LeadForm } from "#lib/domain/lead-form.js";
import { sendEmail } from "../email/index.js";
import { leadReceivedEmail } from "../email/templates/lead-received.js";
import { newLeadAlertEmail } from "../email/templates/new-lead-alert.js";
import { logger } from "../logger.js";

/**
 * Emails the patient and the team about a saved lead. Never throws: the lead is already
 * safely stored, so a failed email is logged for follow-up instead of failing the request.
 */
export async function notifyLeadCreated(lead: { id: string; refNo: number }, form: LeadForm) {
  const ref = formatLeadRef(lead.refNo);
  const results = await Promise.allSettled([
    sendEmail({ to: form.email, ...leadReceivedEmail({ ref, fullName: form.fullName }) }),
    sendEmail({
      to: LEADS_NOTIFY_EMAIL,
      ...newLeadAlertEmail({
        ref,
        intent: form.intent,
        funnel: form.countryCode === "IN" ? "domestic" : "international",
        adminUrl: new URL(`/admin/leads/${lead.id}`, SITE_URL).href
      })
    })
  ]);

  for (const result of results) {
    if (result.status === "rejected") {
      logger.error({ err: result.reason, leadId: lead.id }, "lead notification email failed");
    }
  }
}
