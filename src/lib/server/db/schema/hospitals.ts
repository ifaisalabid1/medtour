import { sql } from "drizzle-orm";
import {
  char,
  check,
  date,
  doublePrecision,
  index,
  integer,
  jsonb,
  pgTable,
  primaryKey,
  smallint,
  text,
  uuid
} from "drizzle-orm/pg-core";
import type { HospitalAmenities } from "#lib/domain/hospitals.js";
import { id, seo, slug, slugFormat, timestamps } from "./columns.js";
import { accreditation, facilityType, mouStatus, publishStatus } from "./enums.js";
import { cities, specialties } from "./taxonomy.js";

export const hospitals = pgTable(
  "hospitals",
  {
    id: id(),
    slug: slug(),
    name: text().notNull(),
    cityId: uuid()
      .notNull()
      .references(() => cities.id, { onDelete: "restrict" }),
    facilityType: facilityType().notNull(),
    accreditations: accreditation().array().notNull().default([]),
    establishedYear: smallint(),
    bedCount: integer(),
    icuBedCount: integer(),
    operatingTheatres: smallint(),
    address: text().notNull(),
    pincode: char({ length: 6 }),
    latitude: doublePrecision(),
    longitude: doublePrecision(),
    airportDistanceKm: smallint(),
    airportTravelMins: smallint(),
    overview: text(),
    technologies: text().array().notNull().default([]), // e.g. ["Da Vinci Xi", "CyberKnife"]
    amenities: jsonb().$type<HospitalAmenities>().notNull().default({}),
    logoKey: text(), // media bucket object key
    coverImageKey: text(),
    status: publishStatus().notNull().default("draft"),
    ...seo,
    ...timestamps
  },
  (t) => [
    slugFormat("hospitals_slug_format", t.slug),
    check("hospitals_pincode_format", sql`${t.pincode} ~ '^[1-9][0-9]{5}$'`),
    check("hospitals_established_year_range", sql`${t.establishedYear} >= 1800`),
    check(
      "hospitals_capacity_non_negative",
      sql`${t.bedCount} >= 0 and ${t.icuBedCount} >= 0 and ${t.operatingTheatres} >= 0`
    ),
    check(
      "hospitals_coordinates_range",
      sql`${t.latitude} between -90 and 90 and ${t.longitude} between -180 and 180`
    ),
    index().on(t.cityId)
  ]
);

/** Admin-only. Public queries must never select from or join this table. */
export const hospitalInternal = pgTable("hospital_internal", {
  hospitalId: uuid()
    .primaryKey()
    .references(() => hospitals.id, { onDelete: "cascade" }),
  mouStatus: mouStatus().notNull().default("none"),
  mouSignedOn: date(),
  mouExpiresOn: date(),
  facilitationTerms: text(),
  internationalDeskEmail: text(),
  internationalDeskPhone: text(),
  notes: text(),
  ...timestamps
});

/** Departments a hospital offers. Powers /hospitals/[specialty]/[city]. */
export const hospitalSpecialties = pgTable(
  "hospital_specialties",
  {
    hospitalId: uuid()
      .notNull()
      .references(() => hospitals.id, { onDelete: "cascade" }),
    specialtyId: uuid()
      .notNull()
      .references(() => specialties.id, { onDelete: "restrict" })
  },
  (t) => [primaryKey({ columns: [t.hospitalId, t.specialtyId] }), index().on(t.specialtyId)]
);
