import { expect } from "vitest";
import { db } from "#lib/server/db/index.js";
import {
  cities,
  doctorHospitals,
  doctorInternal,
  doctorProcedures,
  doctors,
  hospitalInternal,
  hospitalProcedures,
  hospitalProcedureTariffs,
  hospitals,
  hospitalSpecialties,
  medicalReviewers,
  procedures,
  specialties
} from "#lib/server/db/schema/index.js";

/** Values planted in admin-only tables. None of them may ever appear in public output. */
export const SENTINELS = ["987654", "SENTINEL", "sentinel-desk@hospital.example", "+919999999999"];

export function expectNoPrivateData(value: unknown) {
  const json = JSON.stringify(value);
  for (const sentinel of SENTINELS) expect(json).not.toContain(sentinel);
}

/**
 * Seeds a small directory: published and draft rows, plus sentinel values in every
 * admin-only table. `prefix` keeps each test file's rows apart, since files run in
 * parallel against the same test database.
 */
export async function seedDirectory(prefix: string) {
  const slug = (name: string) => `${prefix}-${name}`;

  const [gurugram, chennai] = await db
    .insert(cities)
    .values([
      { slug: slug("gurugram"), name: "Gurugram", state: "Haryana", airportCode: "DEL" },
      { slug: slug("chennai"), name: "Chennai", state: "Tamil Nadu", airportCode: "MAA" }
    ])
    .returning();
  const [cardiology, oncology] = await db
    .insert(specialties)
    .values([
      { slug: slug("cardiology"), name: "Cardiology", sortOrder: 1 },
      { slug: slug("oncology"), name: "Oncology", sortOrder: 2 }
    ])
    .returning();
  await db
    .insert(specialties)
    .values({ slug: slug("cardiac-surgery"), name: "Cardiac Surgery", parentId: cardiology!.id });

  const [reviewer] = await db
    .insert(medicalReviewers)
    .values({
      slug: slug("dr-reviewer"),
      fullName: "Dr Reviewer",
      specialtyId: cardiology!.id,
      qualifications: ["MBBS", "MD"],
      registrationNumber: "NMC-REV-1",
      medicalCouncil: "National Medical Commission",
      status: "published"
    })
    .returning();

  const [heart, , chennaiGeneral] = await db
    .insert(hospitals)
    .values([
      {
        slug: slug("heart-institute"),
        name: "Heart Institute",
        cityId: gurugram!.id,
        facilityType: "super_specialty",
        accreditations: ["nabh", "jci"],
        address: "Sector 1",
        status: "published"
      },
      {
        slug: slug("draft-hospital"),
        name: "Draft Hospital",
        cityId: gurugram!.id,
        facilityType: "multi_specialty",
        address: "Sector 2"
      },
      {
        slug: slug("chennai-general"),
        name: "Chennai General",
        cityId: chennai!.id,
        facilityType: "multi_specialty",
        accreditations: ["nabh"],
        address: "Anna Salai",
        status: "published"
      }
    ])
    .returning();
  await db.insert(hospitalInternal).values({
    hospitalId: heart!.id,
    mouStatus: "signed",
    facilitationTerms: "SENTINEL terms",
    internationalDeskEmail: "sentinel-desk@hospital.example",
    notes: "SENTINEL notes"
  });
  await db.insert(hospitalSpecialties).values([
    { hospitalId: heart!.id, specialtyId: cardiology!.id },
    { hospitalId: chennaiGeneral!.id, specialtyId: oncology!.id }
  ]);

  const verified = {
    medicalCouncil: "Delhi Medical Council",
    registrationVerifiedAt: new Date(),
    status: "published" as const
  };
  const [cardiologist, draftDoctor, oncologist] = await db
    .insert(doctors)
    .values([
      {
        slug: slug("dr-published"),
        fullName: "Dr Published",
        primarySpecialtyId: cardiology!.id,
        registrationNumber: "DMC-1",
        practiceSince: 2001,
        ...verified
      },
      { slug: slug("dr-draft"), fullName: "Dr Draft", primarySpecialtyId: cardiology!.id },
      {
        slug: slug("dr-oncologist"),
        fullName: "Dr Oncologist",
        primarySpecialtyId: oncology!.id,
        registrationNumber: "TNMC-2",
        ...verified
      }
    ])
    .returning();
  await db.insert(doctorInternal).values({
    doctorId: cardiologist!.id,
    opdFeeInr: 987654,
    teleconsultFeeInr: 987654,
    secretaryPhone: "+919999999999",
    notes: "SENTINEL"
  });
  await db.insert(doctorHospitals).values([
    {
      doctorId: cardiologist!.id,
      hospitalId: heart!.id,
      isPrimary: true,
      role: "Director",
      opdSchedule: [{ day: "mon", opens: "10:00", closes: "15:00" }]
    },
    { doctorId: draftDoctor!.id, hospitalId: heart!.id },
    { doctorId: oncologist!.id, hospitalId: chennaiGeneral!.id, isPrimary: true }
  ]);

  const [cabg, draftProcedure] = await db
    .insert(procedures)
    .values([
      {
        slug: slug("cabg"),
        name: "CABG",
        specialtyId: cardiology!.id,
        logistics: { hospitalStayDays: { min: 5, max: 7 } },
        inclusions: ["Pre-operative tests"],
        costFactors: ["Room category"],
        reviewerId: reviewer!.id,
        lastReviewedOn: "2026-10-01",
        status: "published"
      },
      { slug: slug("draft-procedure"), name: "Draft Procedure", specialtyId: cardiology!.id }
    ])
    .returning();
  await db.insert(hospitalProcedures).values([
    { hospitalId: heart!.id, procedureId: cabg!.id, technologies: ["Da Vinci"] },
    { hospitalId: heart!.id, procedureId: draftProcedure!.id }
  ]);
  await db.insert(hospitalProcedureTariffs).values({
    hospitalId: heart!.id,
    procedureId: cabg!.id,
    roomCategory: "single",
    minInr: 987654,
    maxInr: 9876540,
    implantNote: "SENTINEL implant"
  });
  await db.insert(doctorProcedures).values([
    { doctorId: cardiologist!.id, procedureId: cabg!.id },
    { doctorId: draftDoctor!.id, procedureId: cabg!.id }
  ]);

  return { slug };
}
