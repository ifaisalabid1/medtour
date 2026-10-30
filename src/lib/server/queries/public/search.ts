import { and, desc, eq, sql, type AnyColumn, type SQL } from "drizzle-orm";
import { db } from "../../db/index.js";
import { cities, doctors, hospitals, procedures, specialties } from "../../db/schema/index.js";

// PUBLIC DATA ONLY. Site-wide search over specialties and published hospitals, doctors and procedures.
// Full-text search handles word forms and synonyms ("heart bypass" → CABG); trigram
// similarity on names handles typos ("cardiolgy", "appolo").

export const SEARCH_MIN_LENGTH = 2;
export const SEARCH_MAX_LENGTH = 100;

export interface SearchResult {
  type: "specialty" | "hospital" | "doctor" | "procedure";
  slug: string;
  title: string;
  subtitle: string | null;
}

export async function searchDirectory(rawQuery: string, limit = 8): Promise<SearchResult[]> {
  const q = rawQuery.trim().slice(0, SEARCH_MAX_LENGTH);
  if (q.length < SEARCH_MIN_LENGTH) return [];

  // websearch_to_tsquery never throws on user input (quotes, "or", "-word" are all safe)
  const query = sql`websearch_to_tsquery('english', ${q})`;
  const matches = (search: AnyColumn, name: AnyColumn): SQL =>
    sql`(${search} @@ ${query} or ${q} <% ${name})`;
  const score = (search: AnyColumn, name: AnyColumn) =>
    sql<number>`ts_rank(${search}, ${query}) + word_similarity(${q}, ${name})`.mapWith(Number);

  const hospitalScore = score(hospitals.search, hospitals.name);
  const doctorScore = score(doctors.search, doctors.fullName);
  const procedureScore = score(procedures.search, procedures.name);

  // Few specialties: computing their search document on the fly needs no stored column
  const specialtyDocument = sql`to_tsvector('english', ${specialties.name})`;
  const specialtyScore =
    sql<number>`ts_rank(${specialtyDocument}, ${query}) + word_similarity(${q}, ${specialties.name})`.mapWith(
      Number
    );

  const [specialtyRows, hospitalRows, doctorRows, procedureRows] = await Promise.all([
    db
      .select({
        slug: specialties.slug,
        title: specialties.name,
        subtitle: sql<string | null>`null`,
        score: specialtyScore
      })
      .from(specialties)
      .where(sql`(${specialtyDocument} @@ ${query} or ${q} <% ${specialties.name})`)
      .orderBy(desc(specialtyScore))
      .limit(limit),
    db
      .select({
        slug: hospitals.slug,
        title: hospitals.name,
        subtitle: cities.name,
        score: hospitalScore
      })
      .from(hospitals)
      .innerJoin(cities, eq(cities.id, hospitals.cityId))
      .where(and(eq(hospitals.status, "published"), matches(hospitals.search, hospitals.name)))
      .orderBy(desc(hospitalScore))
      .limit(limit),
    db
      .select({
        slug: doctors.slug,
        title: doctors.fullName,
        subtitle: specialties.name,
        score: doctorScore
      })
      .from(doctors)
      .innerJoin(specialties, eq(specialties.id, doctors.primarySpecialtyId))
      .where(and(eq(doctors.status, "published"), matches(doctors.search, doctors.fullName)))
      .orderBy(desc(doctorScore))
      .limit(limit),
    db
      .select({
        slug: procedures.slug,
        title: procedures.name,
        subtitle: specialties.name,
        score: procedureScore
      })
      .from(procedures)
      .innerJoin(specialties, eq(specialties.id, procedures.specialtyId))
      .where(and(eq(procedures.status, "published"), matches(procedures.search, procedures.name)))
      .orderBy(desc(procedureScore))
      .limit(limit)
  ]);

  return [
    ...specialtyRows.map((row) => ({ type: "specialty" as const, ...row })),
    ...hospitalRows.map((row) => ({ type: "hospital" as const, ...row })),
    ...doctorRows.map((row) => ({ type: "doctor" as const, ...row })),
    ...procedureRows.map((row) => ({ type: "procedure" as const, ...row }))
  ]
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map(({ type, slug, title, subtitle }) => ({ type, slug, title, subtitle }));
}
