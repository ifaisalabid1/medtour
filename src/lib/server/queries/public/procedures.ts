import { and, asc, eq } from "drizzle-orm";
import { db } from "../../db/index.js";
import {
  cities,
  doctorProcedures,
  doctors,
  hospitalProcedures,
  hospitals,
  medicalReviewers,
  procedures,
  specialties
} from "../../db/schema/index.js";

// PUBLIC DATA ONLY. Every query lists its columns explicitly and returns published rows only.
// Never import *_internal or tariff tables here: src/lib/server/queries/public/guard.test.ts enforces it.

const isPublished = eq(procedures.status, "published");

/** Procedure index, optionally for one specialty. */
export async function listProcedures(specialtySlug?: string) {
  return db
    .select({
      slug: procedures.slug,
      name: procedures.name,
      summary: procedures.summary,
      specialty: { slug: specialties.slug, name: specialties.name }
    })
    .from(procedures)
    .innerJoin(specialties, eq(specialties.id, procedures.specialtyId))
    .where(and(isPublished, specialtySlug ? eq(specialties.slug, specialtySlug) : undefined))
    .orderBy(asc(procedures.name));
}

export type ProcedureListItem = Awaited<ReturnType<typeof listProcedures>>[number];

/** Everything the public procedure guide shows, or null if not found / not published. */
export async function getProcedureGuide(slug: string) {
  const [row] = await db
    .select({
      id: procedures.id,
      slug: procedures.slug,
      name: procedures.name,
      alsoKnownAs: procedures.alsoKnownAs,
      summary: procedures.summary,
      procedureType: procedures.procedureType,
      logistics: procedures.logistics,
      eligibility: procedures.eligibility,
      risks: procedures.risks,
      inclusions: procedures.inclusions,
      costFactors: procedures.costFactors,
      faqs: procedures.faqs,
      body: procedures.body,
      metaTitle: procedures.metaTitle,
      metaDescription: procedures.metaDescription,
      updatedAt: procedures.updatedAt,
      specialty: { slug: specialties.slug, name: specialties.name },
      lastReviewedOn: procedures.lastReviewedOn,
      // Joined only when the reviewer's own profile is published
      reviewer: {
        slug: medicalReviewers.slug,
        fullName: medicalReviewers.fullName,
        qualifications: medicalReviewers.qualifications,
        affiliation: medicalReviewers.affiliation,
        registrationNumber: medicalReviewers.registrationNumber,
        medicalCouncil: medicalReviewers.medicalCouncil,
        profileUrls: medicalReviewers.profileUrls
      }
    })
    .from(procedures)
    .innerJoin(specialties, eq(specialties.id, procedures.specialtyId))
    .leftJoin(
      medicalReviewers,
      and(eq(medicalReviewers.id, procedures.reviewerId), eq(medicalReviewers.status, "published"))
    )
    .where(and(eq(procedures.slug, slug), isPublished));

  if (!row) return null;
  const { id, reviewer, lastReviewedOn, ...guide } = row;

  const [offeredAt, performedBy] = await Promise.all([
    db
      .select({
        slug: hospitals.slug,
        name: hospitals.name,
        accreditations: hospitals.accreditations,
        city: { slug: cities.slug, name: cities.name },
        technologies: hospitalProcedures.technologies
      })
      .from(hospitalProcedures)
      .innerJoin(hospitals, eq(hospitals.id, hospitalProcedures.hospitalId))
      .innerJoin(cities, eq(cities.id, hospitals.cityId))
      .where(and(eq(hospitalProcedures.procedureId, id), eq(hospitals.status, "published")))
      .orderBy(asc(hospitals.name)),

    db
      .select({
        slug: doctors.slug,
        fullName: doctors.fullName,
        designation: doctors.designation,
        registrationNumber: doctors.registrationNumber,
        medicalCouncil: doctors.medicalCouncil
      })
      .from(doctorProcedures)
      .innerJoin(doctors, eq(doctors.id, doctorProcedures.doctorId))
      .where(and(eq(doctorProcedures.procedureId, id), eq(doctors.status, "published")))
      .orderBy(asc(doctors.fullName))
  ]);

  return {
    ...guide,
    // A review is shown only with a published reviewer (E-E-A-T attribution)
    review: reviewer && lastReviewedOn ? { reviewer, lastReviewedOn } : null,
    hospitals: offeredAt,
    doctors: performedBy
  };
}

export type ProcedureGuide = NonNullable<Awaited<ReturnType<typeof getProcedureGuide>>>;
