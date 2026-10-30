import { sql } from "drizzle-orm";
import {
  char,
  check,
  index,
  pgTable,
  smallint,
  text,
  uuid,
  type AnyPgColumn
} from "drizzle-orm/pg-core";
import { id, seo, slug, slugFormat, timestamps } from "./columns.js";

export const cities = pgTable(
  "cities",
  {
    id: id(),
    slug: slug(),
    name: text().notNull(),
    state: text().notNull(),
    airportCode: char({ length: 3 }), // IATA code, e.g. DEL
    airportName: text(),
    summary: text(),
    sortOrder: smallint().notNull().default(0),
    ...seo,
    ...timestamps
  },
  (t) => [
    slugFormat("cities_slug_format", t.slug),
    check("cities_airport_code_format", sql`${t.airportCode} ~ '^[A-Z]{3}$'`)
  ]
);

export const specialties = pgTable(
  "specialties",
  {
    id: id(),
    slug: slug(),
    name: text().notNull(),
    // Sub-specialties, e.g. Cardiac Surgery under Cardiology
    parentId: uuid().references((): AnyPgColumn => specialties.id, { onDelete: "restrict" }),
    summary: text(),
    icon: text(), // lucide icon name
    sortOrder: smallint().notNull().default(0),
    ...seo,
    ...timestamps
  },
  (t) => [
    slugFormat("specialties_slug_format", t.slug),
    check("specialties_not_own_parent", sql`${t.parentId} <> ${t.id}`),
    index().on(t.parentId)
  ]
);
