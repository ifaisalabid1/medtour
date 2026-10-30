import { and, arrayContains, asc, eq, inArray, type SQL } from "drizzle-orm";
import type { Accreditation } from "#lib/domain/hospitals.js";
import { db } from "../../db/index.js";
import {
  cities,
  doctorHospitals,
  doctors,
  hospitalProcedures,
  hospitals,
  hospitalSpecialties,
  procedures,
  specialties
} from "../../db/schema/index.js";

// PUBLIC DATA ONLY. Every query lists its columns explicitly and returns published rows only.
// Never import *_internal or tariff tables here: src/lib/server/queries/public/guard.test.ts enforces it.

const isPublished = eq(hospitals.status, "published");

/** Columns shown on directory cards. */
const cardColumns = {
  slug: hospitals.slug,
  name: hospitals.name,
  facilityType: hospitals.facilityType,
  accreditations: hospitals.accreditations,
  establishedYear: hospitals.establishedYear,
  bedCount: hospitals.bedCount,
  airportDistanceKm: hospitals.airportDistanceKm,
  city: { slug: cities.slug, name: cities.name }
};

export interface HospitalFilters {
  citySlug?: string;
  specialtySlug?: string;
  accreditation?: Accreditation;
}

function filtersToSql({
  citySlug,
  specialtySlug,
  accreditation
}: HospitalFilters): SQL | undefined {
  return and(
    isPublished,
    citySlug
      ? inArray(
          hospitals.cityId,
          db.select({ id: cities.id }).from(cities).where(eq(cities.slug, citySlug))
        )
      : undefined,
    specialtySlug
      ? inArray(
          hospitals.id,
          db
            .select({ id: hospitalSpecialties.hospitalId })
            .from(hospitalSpecialties)
            .innerJoin(specialties, eq(specialties.id, hospitalSpecialties.specialtyId))
            .where(eq(specialties.slug, specialtySlug))
        )
      : undefined,
    accreditation ? arrayContains(hospitals.accreditations, [accreditation]) : undefined
  );
}

export const HOSPITALS_PAGE_SIZE = 20;

/** Directory listing. Sorted alphabetically: NMC rules forbid paid or "best" ranking. */
export async function listHospitals(filters: HospitalFilters = {}, page = 1) {
  const where = filtersToSql(filters);
  const offset = (Math.max(1, Math.floor(page)) - 1) * HOSPITALS_PAGE_SIZE;

  const [items, total] = await Promise.all([
    db
      .select(cardColumns)
      .from(hospitals)
      .innerJoin(cities, eq(cities.id, hospitals.cityId))
      .where(where)
      .orderBy(asc(hospitals.name))
      .limit(HOSPITALS_PAGE_SIZE)
      .offset(offset),
    db.$count(hospitals, where)
  ]);

  return { items, total, pageSize: HOSPITALS_PAGE_SIZE };
}

export type HospitalCard = Awaited<ReturnType<typeof listHospitals>>["items"][number];

/** Everything the public hospital profile page shows, or null if not found / not published. */
export async function getHospitalProfile(slug: string) {
  const [hospital] = await db
    .select({
      id: hospitals.id,
      ...cardColumns,
      icuBedCount: hospitals.icuBedCount,
      operatingTheatres: hospitals.operatingTheatres,
      address: hospitals.address,
      pincode: hospitals.pincode,
      latitude: hospitals.latitude,
      longitude: hospitals.longitude,
      airportTravelMins: hospitals.airportTravelMins,
      overview: hospitals.overview,
      technologies: hospitals.technologies,
      amenities: hospitals.amenities,
      metaTitle: hospitals.metaTitle,
      metaDescription: hospitals.metaDescription,
      updatedAt: hospitals.updatedAt,
      city: {
        slug: cities.slug,
        name: cities.name,
        state: cities.state,
        airportCode: cities.airportCode,
        airportName: cities.airportName
      }
    })
    .from(hospitals)
    .innerJoin(cities, eq(cities.id, hospitals.cityId))
    .where(and(eq(hospitals.slug, slug), isPublished));

  if (!hospital) return null;
  const { id, ...profile } = hospital; // the internal id is used for the joins below, never returned

  const [departments, team, treatments] = await Promise.all([
    db
      .select({ slug: specialties.slug, name: specialties.name })
      .from(hospitalSpecialties)
      .innerJoin(specialties, eq(specialties.id, hospitalSpecialties.specialtyId))
      .where(eq(hospitalSpecialties.hospitalId, id))
      .orderBy(asc(specialties.sortOrder), asc(specialties.name)),

    db
      .select({
        slug: doctors.slug,
        fullName: doctors.fullName,
        designation: doctors.designation,
        qualifications: doctors.qualifications,
        practiceSince: doctors.practiceSince,
        registrationNumber: doctors.registrationNumber,
        medicalCouncil: doctors.medicalCouncil,
        role: doctorHospitals.role,
        specialty: specialties.name
      })
      .from(doctorHospitals)
      .innerJoin(doctors, eq(doctors.id, doctorHospitals.doctorId))
      .innerJoin(specialties, eq(specialties.id, doctors.primarySpecialtyId))
      .where(and(eq(doctorHospitals.hospitalId, id), eq(doctors.status, "published")))
      .orderBy(asc(doctors.fullName)),

    db
      .select({
        slug: procedures.slug,
        name: procedures.name,
        technologies: hospitalProcedures.technologies
      })
      .from(hospitalProcedures)
      .innerJoin(procedures, eq(procedures.id, hospitalProcedures.procedureId))
      .where(and(eq(hospitalProcedures.hospitalId, id), eq(procedures.status, "published")))
      .orderBy(asc(procedures.name))
  ]);

  return { ...profile, specialties: departments, doctors: team, procedures: treatments };
}

export type HospitalProfile = NonNullable<Awaited<ReturnType<typeof getHospitalProfile>>>;
