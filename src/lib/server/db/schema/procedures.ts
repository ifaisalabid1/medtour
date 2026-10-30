import { sql, type SQL } from "drizzle-orm";
import {
  check,
  date,
  foreignKey,
  index,
  integer,
  jsonb,
  pgTable,
  primaryKey,
  text,
  uuid
} from "drizzle-orm/pg-core";
import type { ProcedureFaq, ProcedureLogistics } from "#lib/domain/procedures.js";
import { id, seo, slug, slugFormat, timestamps, tsvector } from "./columns.js";
import { doctors } from "./doctors.js";
import { publishStatus, roomCategory } from "./enums.js";
import { hospitals } from "./hospitals.js";
import { medicalReviewers } from "./reviewers.js";
import { specialties } from "./taxonomy.js";

export const procedures = pgTable(
  "procedures",
  {
    id: id(),
    slug: slug(),
    name: text().notNull(),
    specialtyId: uuid()
      .notNull()
      .references(() => specialties.id, { onDelete: "restrict" }),
    alsoKnownAs: text().array().notNull().default([]), // synonyms, used by search
    summary: text(),
    procedureType: text(), // e.g. "Minimally invasive (laparoscopic)"
    logistics: jsonb().$type<ProcedureLogistics>().notNull().default({}),
    eligibility: text(),
    risks: text(),
    inclusions: text().array().notNull().default([]), // what a standard package covers
    costFactors: text().array().notNull().default([]), // what changes the final bill, without numbers
    faqs: jsonb().$type<ProcedureFaq[]>().notNull().default([]),
    body: text(), // long-form guide, sanitised HTML (added with the editor later)
    reviewerId: uuid().references(() => medicalReviewers.id, { onDelete: "restrict" }),
    lastReviewedOn: date(),
    search: tsvector().generatedAlwaysAs(
      (): SQL =>
        sql`setweight(to_tsvector('english', ${procedures.name} || ' ' || immutable_array_to_string(${procedures.alsoKnownAs})), 'A') || setweight(to_tsvector('english', coalesce(${procedures.summary}, '') || ' ' || coalesce(${procedures.procedureType}, '')), 'B')`
    ),
    status: publishStatus().notNull().default("draft"),
    ...seo,
    ...timestamps
  },
  (t) => [
    slugFormat("procedures_slug_format", t.slug),
    // A review needs both who and when, or neither
    check(
      "procedures_review_complete",
      sql`(${t.reviewerId} is null) = (${t.lastReviewedOn} is null)`
    ),
    index().on(t.specialtyId),
    index().on(t.reviewerId),
    index().using("gin", t.search),
    index("procedures_name_trgm_index").using("gin", t.name.op("gin_trgm_ops"))
  ]
);

/** Which hospitals offer which procedures. Public. */
export const hospitalProcedures = pgTable(
  "hospital_procedures",
  {
    hospitalId: uuid()
      .notNull()
      .references(() => hospitals.id, { onDelete: "cascade" }),
    procedureId: uuid()
      .notNull()
      .references(() => procedures.id, { onDelete: "cascade" }),
    technologies: text().array().notNull().default([]), // e.g. ["Da Vinci Xi"]
    notes: text()
  },
  (t) => [primaryKey({ columns: [t.hospitalId, t.procedureId] }), index().on(t.procedureId)]
);

/** Procedures a doctor performs. Powers /doctors/[specialty]/[procedure]/[city]. */
export const doctorProcedures = pgTable(
  "doctor_procedures",
  {
    doctorId: uuid()
      .notNull()
      .references(() => doctors.id, { onDelete: "cascade" }),
    procedureId: uuid()
      .notNull()
      .references(() => procedures.id, { onDelete: "cascade" })
  },
  (t) => [primaryKey({ columns: [t.doctorId, t.procedureId] }), index().on(t.procedureId)]
);

/**
 * Admin-only negotiated prices, used to build private quotes.
 * Public queries must never select from or join this table.
 */
export const hospitalProcedureTariffs = pgTable(
  "hospital_procedure_tariffs",
  {
    hospitalId: uuid().notNull(),
    procedureId: uuid().notNull(),
    roomCategory: roomCategory().notNull(),
    minInr: integer().notNull(),
    maxInr: integer().notNull(),
    inclusionsNote: text(),
    implantNote: text(),
    validUntil: date(),
    ...timestamps
  },
  (t) => [
    // Explicit name: the generated one is over Postgres' 63-char identifier limit
    primaryKey({
      name: "hospital_procedure_tariffs_pk",
      columns: [t.hospitalId, t.procedureId, t.roomCategory]
    }),
    // Prices can only exist for a procedure the hospital actually offers
    foreignKey({
      name: "hospital_procedure_tariffs_offering_fk",
      columns: [t.hospitalId, t.procedureId],
      foreignColumns: [hospitalProcedures.hospitalId, hospitalProcedures.procedureId]
    }).onDelete("cascade"),
    check(
      "hospital_procedure_tariffs_range_valid",
      sql`${t.minInr} >= 0 and ${t.maxInr} >= ${t.minInr}`
    )
  ]
);
