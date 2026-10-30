import { sql } from "drizzle-orm";
import { check, index, pgTable, smallint, text, uuid } from "drizzle-orm/pg-core";
import { id, slug, slugFormat, timestamps } from "./columns.js";
import { publishStatus } from "./enums.js";
import { specialties } from "./taxonomy.js";

export const medicalReviewers = pgTable(
  "medical_reviewers",
  {
    id: id(),
    slug: slug(),
    fullName: text().notNull(),
    specialtyId: uuid()
      .notNull()
      .references(() => specialties.id, { onDelete: "restrict" }),
    qualifications: text().array().notNull().default([]), // e.g. ["MBBS", "MD"]
    affiliation: text(),
    practiceSince: smallint(), // years of experience are derived, so they never go stale
    registrationNumber: text().notNull(), // NMC / State Medical Council
    medicalCouncil: text().notNull(),
    bio: text(),
    profileUrls: text().array().notNull().default([]), // schema.org sameAs links
    status: publishStatus().notNull().default("draft"),
    ...timestamps
  },
  (t) => [
    slugFormat("medical_reviewers_slug_format", t.slug),
    check("medical_reviewers_practice_since_range", sql`${t.practiceSince} >= 1950`),
    index().on(t.specialtyId)
  ]
);
