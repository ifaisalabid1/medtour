import { beforeAll, describe, expect, test } from "vitest";
import { expectNoPrivateData, seedDirectory } from "#test/fixtures/directory.js";
import { getDoctorProfile, listDoctors } from "./doctors.js";

let slug: (name: string) => string;

beforeAll(async () => {
  ({ slug } = await seedDirectory("pd"));
});

describe("getDoctorProfile", () => {
  test("returns registration, affiliations with OPD schedule, and procedures", async () => {
    const profile = await getDoctorProfile(slug("dr-published"));

    expect(profile).toMatchObject({
      fullName: "Dr Published",
      registrationNumber: "DMC-1",
      medicalCouncil: "Delhi Medical Council",
      specialty: { slug: slug("cardiology") },
      hospitals: [
        {
          slug: slug("heart-institute"),
          isPrimary: true,
          opdSchedule: [{ day: "mon", opens: "10:00", closes: "15:00" }]
        }
      ],
      procedures: [{ slug: slug("cabg") }]
    });
    expect(profile).not.toHaveProperty("id");
  });

  test("never contains admin-only data", async () => {
    expectNoPrivateData(await getDoctorProfile(slug("dr-published")));
  });

  test("returns null for draft doctors", async () => {
    expect(await getDoctorProfile(slug("dr-draft"))).toBeNull();
  });
});

describe("listDoctors", () => {
  test("filters by specialty, procedure and city, published only", async () => {
    const bySpecialty = await listDoctors({ specialtySlug: slug("cardiology") });
    expect(bySpecialty.items.map((d) => d.slug)).toEqual([slug("dr-published")]);
    expect(bySpecialty.total).toBe(1);

    const byProcedure = await listDoctors({ procedureSlug: slug("cabg") });
    expect(byProcedure.items.map((d) => d.slug)).toEqual([slug("dr-published")]);

    const byCity = await listDoctors({ citySlug: slug("chennai") });
    expect(byCity.items.map((d) => d.slug)).toEqual([slug("dr-oncologist")]);
  });

  test("shows the primary hospital on the card", async () => {
    const { items } = await listDoctors({
      procedureSlug: slug("cabg"),
      citySlug: slug("gurugram")
    });
    expect(items[0]?.hospital).toEqual({
      slug: slug("heart-institute"),
      name: "Heart Institute",
      city: "Gurugram"
    });
  });

  test("never contains admin-only data", async () => {
    expectNoPrivateData(await listDoctors());
  });
});
