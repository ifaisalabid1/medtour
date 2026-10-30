import { and, asc, desc, eq, inArray, type SQL } from "drizzle-orm";
import { db } from "../../db/index.js";
import {
  cities,
  doctorHospitals,
  doctorProcedures,
  doctors,
  hospitals,
  procedures,
  specialties
} from "../../db/schema/index.js";

// PUBLIC DATA ONLY. Every query lists its columns explicitly and returns published rows only.
// Never import *_internal or tariff tables here: src/lib/server/queries/public/guard.test.ts enforces it.

const isPublished = eq(doctors.status, "published");

/** Shown on every doctor card. NMC requires the registration number wherever a doctor is listed. */
const cardColumns = {
  slug: doctors.slug,
  fullName: doctors.fullName,
  designation: doctors.designation,
  qualifications: doctors.qualifications,
  practiceSince: doctors.practiceSince,
  registrationNumber: doctors.registrationNumber,
  medicalCouncil: doctors.medicalCouncil,
  specialty: { slug: specialties.slug, name: specialties.name }
};

export interface DoctorFilters {
  specialtySlug?: string;
  procedureSlug?: string;
  citySlug?: string;
}

function filtersToSql({ specialtySlug, procedureSlug, citySlug }: DoctorFilters): SQL | undefined {
  return and(
    isPublished,
    specialtySlug
      ? inArray(
          doctors.primarySpecialtyId,
          db
            .select({ id: specialties.id })
            .from(specialties)
            .where(eq(specialties.slug, specialtySlug))
        )
      : undefined,
    procedureSlug
      ? inArray(
          doctors.id,
          db
            .select({ id: doctorProcedures.doctorId })
            .from(doctorProcedures)
            .innerJoin(procedures, eq(procedures.id, doctorProcedures.procedureId))
            .where(eq(procedures.slug, procedureSlug))
        )
      : undefined,
    citySlug
      ? inArray(
          doctors.id,
          db
            .select({ id: doctorHospitals.doctorId })
            .from(doctorHospitals)
            .innerJoin(hospitals, eq(hospitals.id, doctorHospitals.hospitalId))
            .innerJoin(cities, eq(cities.id, hospitals.cityId))
            .where(and(eq(cities.slug, citySlug), eq(hospitals.status, "published")))
        )
      : undefined
  );
}

export const DOCTORS_PAGE_SIZE = 20;

/** Directory listing. Sorted alphabetically: NMC rules forbid paid or "best" ranking. */
export async function listDoctors(filters: DoctorFilters = {}, page = 1) {
  const where = filtersToSql(filters);
  const offset = (Math.max(1, Math.floor(page)) - 1) * DOCTORS_PAGE_SIZE;

  const [items, total] = await Promise.all([
    db
      .select({
        ...cardColumns,
        // Primary affiliation, if that hospital is published
        hospital: { slug: hospitals.slug, name: hospitals.name, city: cities.name }
      })
      .from(doctors)
      .innerJoin(specialties, eq(specialties.id, doctors.primarySpecialtyId))
      .leftJoin(
        doctorHospitals,
        and(eq(doctorHospitals.doctorId, doctors.id), eq(doctorHospitals.isPrimary, true))
      )
      .leftJoin(
        hospitals,
        and(eq(hospitals.id, doctorHospitals.hospitalId), eq(hospitals.status, "published"))
      )
      .leftJoin(cities, eq(cities.id, hospitals.cityId))
      .where(where)
      .orderBy(asc(doctors.fullName))
      .limit(DOCTORS_PAGE_SIZE)
      .offset(offset),
    db.$count(doctors, where)
  ]);

  return { items, total, pageSize: DOCTORS_PAGE_SIZE };
}

export type DoctorCard = Awaited<ReturnType<typeof listDoctors>>["items"][number];

/** Everything the public doctor profile page shows, or null if not found / not published. */
export async function getDoctorProfile(slug: string) {
  const [doctor] = await db
    .select({
      id: doctors.id,
      ...cardColumns,
      bio: doctors.bio,
      languages: doctors.languages,
      clinicalFocus: doctors.clinicalFocus,
      education: doctors.education,
      awards: doctors.awards,
      workHistory: doctors.workHistory,
      metaTitle: doctors.metaTitle,
      metaDescription: doctors.metaDescription,
      updatedAt: doctors.updatedAt
    })
    .from(doctors)
    .innerJoin(specialties, eq(specialties.id, doctors.primarySpecialtyId))
    .where(and(eq(doctors.slug, slug), isPublished));

  if (!doctor) return null;
  const { id, ...profile } = doctor; // used for the joins below, never returned

  const [affiliations, treatments] = await Promise.all([
    db
      .select({
        slug: hospitals.slug,
        name: hospitals.name,
        city: { slug: cities.slug, name: cities.name },
        role: doctorHospitals.role,
        isPrimary: doctorHospitals.isPrimary,
        opdSchedule: doctorHospitals.opdSchedule
      })
      .from(doctorHospitals)
      .innerJoin(hospitals, eq(hospitals.id, doctorHospitals.hospitalId))
      .innerJoin(cities, eq(cities.id, hospitals.cityId))
      .where(and(eq(doctorHospitals.doctorId, id), eq(hospitals.status, "published")))
      .orderBy(desc(doctorHospitals.isPrimary), asc(hospitals.name)),

    db
      .select({ slug: procedures.slug, name: procedures.name })
      .from(doctorProcedures)
      .innerJoin(procedures, eq(procedures.id, doctorProcedures.procedureId))
      .where(and(eq(doctorProcedures.doctorId, id), eq(procedures.status, "published")))
      .orderBy(asc(procedures.name))
  ]);

  return { ...profile, hospitals: affiliations, procedures: treatments };
}

export type DoctorProfile = NonNullable<Awaited<ReturnType<typeof getDoctorProfile>>>;
