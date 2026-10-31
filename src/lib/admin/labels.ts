import type { LeadIntent, LeadStatus } from "#lib/domain/leads.js";

/** Display names for enum values shown in the admin panel. */

export const LEAD_STATUS_LABELS: Record<LeadStatus, string> = {
  new: "New",
  contacted: "Contacted",
  awaiting_documents: "Awaiting documents",
  under_review: "Under review",
  quote_sent: "Quote sent",
  converted: "Converted",
  closed: "Closed",
  spam: "Spam"
};

export const LEAD_INTENT_LABELS: Record<LeadIntent, string> = {
  treatment: "Treatment",
  second_opinion: "Second opinion",
  teleconsult: "Teleconsult",
  medical_visa: "Medical visa",
  other: "Other"
};

export const PUBLISH_STATUS_LABELS = {
  draft: "Draft",
  published: "Published",
  archived: "Archived"
} as const;
