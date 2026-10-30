import { sql } from "drizzle-orm";
import {
  boolean,
  char,
  check,
  index,
  inet,
  integer,
  jsonb,
  pgTable,
  text,
  timestamp,
  uuid
} from "drizzle-orm/pg-core";
import type { ConsentPurpose, UtmParams } from "#lib/domain/leads.js";
import { id, timestamps } from "./columns.js";
import { doctors } from "./doctors.js";
import { documentKind, leadIntent, leadStatus, reportsStatus, travelTimeline } from "./enums.js";
import { hospitals } from "./hospitals.js";
import { procedures } from "./procedures.js";

export const patientLeads = pgTable(
  "patient_leads",
  {
    id: id(),
    // Human-friendly reference for WhatsApp and email, e.g. "MT-1001"
    refNo: integer().generatedAlwaysAsIdentity({ startWith: 1001 }).unique(),
    // Personal data: nullable only so a lead can be anonymised (see check below)
    fullName: text(),
    email: text(),
    phone: text(), // E.164, e.g. +919876543210
    description: text(), // the patient's own description of the medical problem
    countryCode: char({ length: 2 }).notNull(), // ISO 3166-1 alpha-2 country of residence
    indianState: text(), // domestic funnel
    passportCountry: char({ length: 2 }), // international funnel (visa rules)
    intent: leadIntent().notNull(),
    reportsStatus: reportsStatus(),
    travelTimeline: travelTimeline(),
    needsVisaLetter: boolean().notNull().default(false),
    openToPaidTeleconsult: boolean().notNull().default(false),
    needsInsuranceHelp: boolean().notNull().default(false),
    // Page context the enquiry came from
    procedureId: uuid().references(() => procedures.id, { onDelete: "set null" }),
    hospitalId: uuid().references(() => hospitals.id, { onDelete: "set null" }),
    doctorId: uuid().references(() => doctors.id, { onDelete: "set null" }),
    sourcePath: text(),
    utm: jsonb().$type<UtmParams>().notNull().default({}),
    status: leadStatus().notNull().default("new"),
    anonymizedAt: timestamp({ withTimezone: true }),
    ...timestamps
  },
  (t) => [
    check(
      "patient_leads_pii_present",
      sql`${t.anonymizedAt} is not null or (${t.fullName} is not null and ${t.email} is not null and ${t.phone} is not null and ${t.description} is not null)`
    ),
    check("patient_leads_phone_e164", sql`${t.phone} ~ '^\\+[1-9][0-9]{6,14}$'`),
    check(
      "patient_leads_country_code_format",
      sql`${t.countryCode} ~ '^[A-Z]{2}$' and ${t.passportCountry} ~ '^[A-Z]{2}$'`
    ),
    check(
      "patient_leads_domestic_has_state",
      sql`${t.countryCode} <> 'IN' or ${t.indianState} is not null`
    ),
    index().on(t.status, t.createdAt), // admin inbox: filter by status, newest first
    index().on(t.email),
    index().on(t.phone)
  ]
);

/** Proof of consent. Kept after anonymisation; blocks hard-deleting the lead. */
export const consentRecords = pgTable(
  "consent_records",
  {
    id: id(),
    leadId: uuid()
      .notNull()
      .references(() => patientLeads.id, { onDelete: "restrict" }),
    noticeVersion: text().notNull(),
    noticeSha256: char({ length: 64 }).notNull(), // hash of the exact notice text shown
    purposes: text().array().$type<ConsentPurpose[]>().notNull(),
    grantedAt: timestamp({ withTimezone: true }).notNull().defaultNow(),
    withdrawnAt: timestamp({ withTimezone: true }),
    ipAddress: inet(),
    userAgent: text()
  },
  (t) => [
    check("consent_records_withdrawn_after_granted", sql`${t.withdrawnAt} >= ${t.grantedAt}`),
    check("consent_records_has_purposes", sql`cardinality(${t.purposes}) > 0`),
    index().on(t.leadId)
  ]
);

/** Metadata for files in the private R2 bucket. The files themselves never touch this database. */
export const patientDocuments = pgTable(
  "patient_documents",
  {
    id: id(),
    leadId: uuid()
      .notNull()
      .references(() => patientLeads.id, { onDelete: "restrict" }),
    kind: documentKind().notNull(),
    objectKey: text().notNull().unique(), // e.g. leads/{leadId}/{uuid}.pdf
    originalFilename: text().notNull(),
    mimeType: text().notNull(),
    sizeBytes: integer().notNull(),
    uploadedAt: timestamp({ withTimezone: true }), // null until the direct upload is confirmed
    ...timestamps
  },
  (t) => [check("patient_documents_size_positive", sql`${t.sizeBytes} > 0`), index().on(t.leadId)]
);
