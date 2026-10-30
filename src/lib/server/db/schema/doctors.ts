import { sql } from "drizzle-orm";
import {
  boolean,
  check,
  index,
  integer,
  jsonb,
  pgTable,
  primaryKey,
  smallint,
  text,
  timestamp,
  uniqueIndex,
  uuid
} from "drizzle-orm/pg-core";
import type { AwardEntry, EducationEntry, OpdSlot, WorkEntry } from "#lib/domain/doctors.js";
import { id, seo, slug, slugFormat, timestamps } from "./columns.js";
import { publishStatus } from "./enums.js";
import { hospitals } from "./hospitals.js";
import { specialties } from "./taxonomy.js";

export const doctors = pgTable(
  "doctors",
  {
    id: id(),
    slug: slug(),
    fullName: text().notNull(),
    designation: text(), // e.g. "Senior Consultant"
    primarySpecialtyId: uuid()
      .notNull()
      .references(() => specialties.id, { onDelete: "restrict" }),
    qualifications: text().array().notNull().default([]),
    practiceSince: smallint(),
    registrationNumber: text(), // NMC / State Medical Council
    medicalCouncil: text(),
    registrationVerifiedAt: timestamp({ withTimezone: true }), // set by staff after checking the register
    bio: text(),
    languages: text().array().notNull().default([]),
    clinicalFocus: text().array().notNull().default([]),
    education: jsonb().$type<EducationEntry[]>().notNull().default([]),
    awards: jsonb().$type<AwardEntry[]>().notNull().default([]),
    workHistory: jsonb().$type<WorkEntry[]>().notNull().default([]),
    status: publishStatus().notNull().default("draft"),
    ...seo,
    ...timestamps
  },
  (t) => [
    slugFormat("doctors_slug_format", t.slug),
    check("doctors_practice_since_range", sql`${t.practiceSince} >= 1950`),
    // NMC: a public doctor profile must show a verified registration number
    check(
      "doctors_published_requires_verified_registration",
      sql`${t.status} <> 'published' or (${t.registrationNumber} is not null and ${t.medicalCouncil} is not null and ${t.registrationVerifiedAt} is not null)`
    ),
    index().on(t.primarySpecialtyId)
  ]
);

/** Admin-only. Fees exist for quoting, never for public pages. */
export const doctorInternal = pgTable(
  "doctor_internal",
  {
    doctorId: uuid()
      .primaryKey()
      .references(() => doctors.id, { onDelete: "cascade" }),
    opdFeeInr: integer(),
    teleconsultFeeInr: integer(),
    secretaryPhone: text(),
    escalationEmail: text(),
    notes: text(),
    ...timestamps
  },
  (t) => [
    check(
      "doctor_internal_fees_non_negative",
      sql`${t.opdFeeInr} >= 0 and ${t.teleconsultFeeInr} >= 0`
    )
  ]
);

export const doctorHospitals = pgTable(
  "doctor_hospitals",
  {
    doctorId: uuid()
      .notNull()
      .references(() => doctors.id, { onDelete: "cascade" }),
    hospitalId: uuid()
      .notNull()
      .references(() => hospitals.id, { onDelete: "cascade" }),
    role: text(),
    isPrimary: boolean().notNull().default(false),
    opdSchedule: jsonb().$type<OpdSlot[]>().notNull().default([])
  },
  (t) => [
    primaryKey({ columns: [t.doctorId, t.hospitalId] }),
    index().on(t.hospitalId),
    // At most one primary affiliation per doctor
    uniqueIndex("doctor_hospitals_one_primary")
      .on(t.doctorId)
      .where(sql`${t.isPrimary}`)
  ]
);
