import { and, eq } from "drizzle-orm";
import { paths } from "#lib/paths.js";
import { db } from "../../db/index.js";
import {
  cities,
  doctorHospitals,
  doctors,
  hospitals,
  hospitalSpecialties,
  procedures,
  specialties
} from "../../db/schema/index.js";

// PUBLIC DATA ONLY. Every indexable URL. Listing pages appear only when they have at least one
// published result: empty "Cardiology hospitals in Patna" pages are thin content Google penalises.

export interface SitemapEntry {
  path: string;
  lastModified?: Date;
}

const STATIC_PAGES = [
  paths.home(),
  paths.hospitals(),
  paths.doctors(),
  paths.treatments(),
  paths.medicalVisa(),
  paths.reviewerBoard(),
  paths.editorialPolicy(),
  paths.about(),
  paths.contact(),
  paths.privacy()
];

const publishedHospital = eq(hospitals.status, "published");
const publishedDoctor = eq(doctors.status, "published");

export async function listSitemapEntries(): Promise<SitemapEntry[]> {
  const [
    hospitalRows,
    doctorRows,
    procedureRows,
    hospitalCities,
    hospitalSpecialtyCities,
    doctorSpecialtyCities
  ] = await Promise.all([
    db
      .select({ slug: hospitals.slug, updatedAt: hospitals.updatedAt })
      .from(hospitals)
      .where(publishedHospital),
    db
      .select({ slug: doctors.slug, updatedAt: doctors.updatedAt })
      .from(doctors)
      .where(publishedDoctor),
    db
      .select({ slug: procedures.slug, updatedAt: procedures.updatedAt })
      .from(procedures)
      .where(eq(procedures.status, "published")),
    db
      .selectDistinct({ city: cities.slug })
      .from(hospitals)
      .innerJoin(cities, eq(cities.id, hospitals.cityId))
      .where(publishedHospital),
    db
      .selectDistinct({ specialty: specialties.slug, city: cities.slug })
      .from(hospitalSpecialties)
      .innerJoin(
        hospitals,
        and(eq(hospitals.id, hospitalSpecialties.hospitalId), publishedHospital)
      )
      .innerJoin(specialties, eq(specialties.id, hospitalSpecialties.specialtyId))
      .innerJoin(cities, eq(cities.id, hospitals.cityId)),
    db
      .selectDistinct({ specialty: specialties.slug, city: cities.slug })
      .from(doctors)
      .innerJoin(specialties, eq(specialties.id, doctors.primarySpecialtyId))
      .innerJoin(doctorHospitals, eq(doctorHospitals.doctorId, doctors.id))
      .innerJoin(hospitals, and(eq(hospitals.id, doctorHospitals.hospitalId), publishedHospital))
      .innerJoin(cities, eq(cities.id, hospitals.cityId))
      .where(publishedDoctor)
  ]);

  const specialtiesWithContent = new Set([
    ...hospitalSpecialtyCities.map((row) => row.specialty),
    ...doctorSpecialtyCities.map((row) => row.specialty)
  ]);
  const doctorSpecialties = new Set(doctorSpecialtyCities.map((row) => row.specialty));

  return [
    ...STATIC_PAGES.map((path) => ({ path })),
    ...[...specialtiesWithContent].map((slug) => ({ path: paths.specialty(slug) })),
    ...hospitalCities.map(({ city }) => ({ path: paths.hospitalsInCity(city) })),
    ...hospitalSpecialtyCities.map(({ specialty, city }) => ({
      path: paths.hospitalsBySpecialtyInCity(specialty, city)
    })),
    ...[...doctorSpecialties].map((slug) => ({ path: paths.doctorsBySpecialty(slug) })),
    ...doctorSpecialtyCities.map(({ specialty, city }) => ({
      path: paths.doctorsBySpecialtyInCity(specialty, city)
    })),
    ...hospitalRows.map((row) => ({ path: paths.hospital(row.slug), lastModified: row.updatedAt })),
    ...doctorRows.map((row) => ({ path: paths.doctor(row.slug), lastModified: row.updatedAt })),
    ...procedureRows.map((row) => ({
      path: paths.treatment(row.slug),
      lastModified: row.updatedAt
    }))
  ];
}
