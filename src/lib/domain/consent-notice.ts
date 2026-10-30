/**
 * The DPDP consent notice shown next to the lead form (DPDP Rules 2025, Rule 3).
 * DRAFT: have a lawyer review the wording before launch.
 *
 * Bump `version` whenever `text` changes. Each consent record stores the version and a
 * SHA-256 hash of the exact text, so you can prove what every patient agreed to.
 */
export const CONSENT_NOTICE = {
  version: "2026-11-01",
  text: `Consent notice under the Digital Personal Data Protection Act, 2023

Medtour will process the personal data you give us: your name, email address, phone number, country or state of residence, passport country, your description of your medical condition, and any medical reports you upload.

We use it only to:
1. Evaluate your case and suggest suitable hospitals and doctors.
2. Share your details and reports with the partner hospitals we recommend, so they can give a medical opinion, a cost estimate and, where needed, a visa invitation letter.
3. Contact you about your request by WhatsApp, phone and email.
4. If you live outside India: transfer your data between you, us and hospitals in India, as needed for the purposes above.

You can withdraw your consent at any time, as easily as you gave it, from our Privacy page or by emailing our Grievance Officer listed there. We will then stop processing and erase your data, unless a law requires us to keep it. You may also complain to the Data Protection Board of India.`
} as const;
