import { and, asc, count, eq } from "drizzle-orm";
import { alias } from "drizzle-orm/pg-core";
import { db } from "../../db/index.js";
import { cities, hospitals, specialties } from "../../db/schema/index.js";

// PUBLIC DATA ONLY. Cities and specialties for navigation, filters and landing pages.

/** Cities that have at least one published hospital, with how many. */
export async function listCities() {
  return db
    .select({
      slug: cities.slug,
      name: cities.name,
      state: cities.state,
      hospitalCount: count(hospitals.id)
    })
    .from(cities)
    .innerJoin(hospitals, and(eq(hospitals.cityId, cities.id), eq(hospitals.status, "published")))
    .groupBy(cities.id)
    .orderBy(asc(cities.sortOrder), asc(cities.name));
}

export async function getCity(slug: string) {
  const [city] = await db
    .select({
      slug: cities.slug,
      name: cities.name,
      state: cities.state,
      airportCode: cities.airportCode,
      airportName: cities.airportName,
      summary: cities.summary,
      metaTitle: cities.metaTitle,
      metaDescription: cities.metaDescription
    })
    .from(cities)
    .where(eq(cities.slug, slug));
  return city ?? null;
}

const parent = alias(specialties, "parent");

/** All specialties, with the parent's slug for sub-specialties. */
export async function listSpecialties() {
  return db
    .select({
      slug: specialties.slug,
      name: specialties.name,
      summary: specialties.summary,
      icon: specialties.icon,
      parentSlug: parent.slug
    })
    .from(specialties)
    .leftJoin(parent, eq(parent.id, specialties.parentId))
    .orderBy(asc(specialties.sortOrder), asc(specialties.name));
}

export async function getSpecialty(slug: string) {
  const [specialty] = await db
    .select({
      slug: specialties.slug,
      name: specialties.name,
      summary: specialties.summary,
      icon: specialties.icon,
      metaTitle: specialties.metaTitle,
      metaDescription: specialties.metaDescription
    })
    .from(specialties)
    .where(eq(specialties.slug, slug));
  return specialty ?? null;
}
