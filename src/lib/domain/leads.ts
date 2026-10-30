export const LEAD_INTENTS = [
  "treatment",
  "second_opinion",
  "teleconsult",
  "medical_visa",
  "other"
] as const;
export type LeadIntent = (typeof LEAD_INTENTS)[number];

export const TRAVEL_TIMELINES = [
  "within_1_month",
  "in_1_3_months",
  "in_3_6_months",
  "in_6_12_months",
  "not_decided",
  "no_travel"
] as const;
export type TravelTimeline = (typeof TRAVEL_TIMELINES)[number];

export const REPORTS_STATUSES = ["has_reports", "no_reports", "wants_tests_in_india"] as const;
export type ReportsStatus = (typeof REPORTS_STATUSES)[number];

export const LEAD_STATUSES = [
  "new",
  "contacted",
  "awaiting_documents",
  "under_review",
  "quote_sent",
  "converted",
  "closed",
  "spam"
] as const;
export type LeadStatus = (typeof LEAD_STATUSES)[number];

export interface UtmParams {
  source?: string;
  medium?: string;
  campaign?: string;
  term?: string;
  content?: string;
}

/** Each purpose is listed separately in the consent notice (DPDP Rule 3). */
export const CONSENT_PURPOSES = [
  "case_evaluation",
  "share_with_partner_hospitals",
  "contact_whatsapp_email",
  "cross_border_transfer"
] as const;
export type ConsentPurpose = (typeof CONSENT_PURPOSES)[number];

export const DOCUMENT_KINDS = ["medical_report", "prescription", "passport", "other"] as const;
export type DocumentKind = (typeof DOCUMENT_KINDS)[number];
