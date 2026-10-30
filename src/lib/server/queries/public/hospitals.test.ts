import { beforeAll, describe, expect, test } from "vitest";
import { db } from "../../db/index.js";
import {
  cities,
  doctorHospitals,
  doctorInternal,
  doctors,
  hospitalInternal,
  hospitalProcedures,
  hospitalProcedureTariffs,
  hospitals,
  hospitalSpecialties,
  procedures,
  specialties
} from "../../db/schema/index.js";
import { getHospitalProfile, listHospitals } from "./hospitals.js";

// Values planted in admin-only tables. None of them may ever appear in public output.
const SENTINELS = ["987654", "SENTINEL", "sentinel-desk@hospital.example", "+919999999999"];

function expectNoPrivateData(value: unknown) {
  const json = JSON.stringify(value);
  for (const sentinel of SENTINELS) expect(json).not.toContain(sentinel);
}

beforeAll(async () => {
  const [city] = await db
    .insert(cities)
    .values({ slug: "pq-gurugram", name: "Gurugram", state: "Haryana", airportCode: "DEL" })
    .returning();
  const [otherCity] = await db
    .insert(cities)
    .values({ slug: "pq-chennai", name: "Chennai", state: "Tamil Nadu" })
    .returning();
  const [cardio] = await db
    .insert(specialties)
    .values({ slug: "pq-cardiology", name: "Cardiology" })
    .returning();

  const [hospital] = await db
    .insert(hospitals)
    .values([
      {
        slug: "pq-heart-institute",
        name: "Heart Institute",
        cityId: city!.id,
        facilityType: "super_specialty",
        accreditations: ["nabh", "jci"],
        address: "Sector 1",
        status: "published"
      },
      {
        slug: "pq-draft-hospital",
        name: "Draft Hospital",
        cityId: city!.id,
        facilityType: "multi_specialty",
        address: "Sector 2"
      },
      {
        slug: "pq-chennai-general",
        name: "Chennai General",
        cityId: otherCity!.id,
        facilityType: "multi_specialty",
        accreditations: ["nabh"],
        address: "Anna Salai",
        status: "published"
      }
    ])
    .returning();

  await db.insert(hospitalInternal).values({
    hospitalId: hospital!.id,
    mouStatus: "signed",
    facilitationTerms: "SENTINEL terms",
    internationalDeskEmail: "sentinel-desk@hospital.example",
    notes: "SENTINEL notes"
  });
  await db
    .insert(hospitalSpecialties)
    .values({ hospitalId: hospital!.id, specialtyId: cardio!.id });

  const [published, draft] = await db
    .insert(doctors)
    .values([
      {
        slug: "pq-dr-published",
        fullName: "Dr Published",
        primarySpecialtyId: cardio!.id,
        registrationNumber: "DMC-1",
        medicalCouncil: "Delhi Medical Council",
        registrationVerifiedAt: new Date(),
        status: "published"
      },
      { slug: "pq-dr-draft", fullName: "Dr Draft", primarySpecialtyId: cardio!.id }
    ])
    .returning();
  await db.insert(doctorInternal).values({
    doctorId: published!.id,
    opdFeeInr: 987654,
    secretaryPhone: "+919999999999",
    notes: "SENTINEL"
  });
  await db.insert(doctorHospitals).values([
    { doctorId: published!.id, hospitalId: hospital!.id, isPrimary: true, role: "Director" },
    { doctorId: draft!.id, hospitalId: hospital!.id }
  ]);

  const [procedure] = await db
    .insert(procedures)
    .values({ slug: "pq-cabg", name: "CABG", specialtyId: cardio!.id, status: "published" })
    .returning();
  await db
    .insert(hospitalProcedures)
    .values({ hospitalId: hospital!.id, procedureId: procedure!.id, technologies: ["Da Vinci"] });
  await db.insert(hospitalProcedureTariffs).values({
    hospitalId: hospital!.id,
    procedureId: procedure!.id,
    roomCategory: "single",
    minInr: 987654,
    maxInr: 9876540,
    implantNote: "SENTINEL implant"
  });
});

describe("getHospitalProfile", () => {
  test("returns the public profile with departments, doctors and procedures", async () => {
    const profile = await getHospitalProfile("pq-heart-institute");

    expect(profile).toMatchObject({
      name: "Heart Institute",
      accreditations: ["nabh", "jci"],
      city: { slug: "pq-gurugram", airportCode: "DEL" },
      specialties: [{ slug: "pq-cardiology", name: "Cardiology" }],
      doctors: [{ slug: "pq-dr-published", registrationNumber: "DMC-1", role: "Director" }],
      procedures: [{ slug: "pq-cabg", technologies: ["Da Vinci"] }]
    });
    expect(profile).not.toHaveProperty("id");
  });

  test("never contains admin-only data", async () => {
    expectNoPrivateData(await getHospitalProfile("pq-heart-institute"));
  });

  test("hides draft doctors and draft hospitals", async () => {
    const profile = await getHospitalProfile("pq-heart-institute");
    expect(profile?.doctors.map((d) => d.slug)).toEqual(["pq-dr-published"]);
    expect(await getHospitalProfile("pq-draft-hospital")).toBeNull();
  });
});

describe("listHospitals", () => {
  test("filters by city and specialty, published only", async () => {
    const inCity = await listHospitals({ citySlug: "pq-gurugram" });
    expect(inCity.items.map((h) => h.slug)).toEqual(["pq-heart-institute"]);
    expect(inCity.total).toBe(1);

    const cardiology = await listHospitals({ specialtySlug: "pq-cardiology" });
    expect(cardiology.items.map((h) => h.slug)).toEqual(["pq-heart-institute"]);
  });

  test("filters by accreditation", async () => {
    const jci = await listHospitals({ accreditation: "jci" });
    expect(jci.items.map((h) => h.slug)).toEqual(["pq-heart-institute"]);
  });

  test("never contains admin-only data", async () => {
    expectNoPrivateData(await listHospitals());
  });
});
