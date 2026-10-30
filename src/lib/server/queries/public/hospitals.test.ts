import { beforeAll, describe, expect, test } from "vitest";
import { expectNoPrivateData, seedDirectory } from "#test/fixtures/directory.js";
import { getHospitalProfile, listHospitals } from "./hospitals.js";

let slug: (name: string) => string;

beforeAll(async () => {
  ({ slug } = await seedDirectory("ph"));
});

describe("getHospitalProfile", () => {
  test("returns the public profile with departments, doctors and procedures", async () => {
    const profile = await getHospitalProfile(slug("heart-institute"));

    expect(profile).toMatchObject({
      name: "Heart Institute",
      accreditations: ["nabh", "jci"],
      city: { slug: slug("gurugram"), airportCode: "DEL" },
      specialties: [{ slug: slug("cardiology"), name: "Cardiology" }],
      doctors: [{ slug: slug("dr-published"), registrationNumber: "DMC-1", role: "Director" }],
      procedures: [{ slug: slug("cabg"), technologies: ["Da Vinci"] }]
    });
    expect(profile).not.toHaveProperty("id");
  });

  test("never contains admin-only data", async () => {
    expectNoPrivateData(await getHospitalProfile(slug("heart-institute")));
  });

  test("hides draft doctors, procedures and hospitals", async () => {
    const profile = await getHospitalProfile(slug("heart-institute"));
    expect(profile?.doctors.map((d) => d.slug)).toEqual([slug("dr-published")]);
    expect(profile?.procedures.map((p) => p.slug)).toEqual([slug("cabg")]);
    expect(await getHospitalProfile(slug("draft-hospital"))).toBeNull();
  });
});

describe("listHospitals", () => {
  test("filters by city and specialty, published only", async () => {
    const inCity = await listHospitals({ citySlug: slug("gurugram") });
    expect(inCity.items.map((h) => h.slug)).toEqual([slug("heart-institute")]);
    expect(inCity.total).toBe(1);

    const oncology = await listHospitals({ specialtySlug: slug("oncology") });
    expect(oncology.items.map((h) => h.slug)).toEqual([slug("chennai-general")]);
  });

  test("filters by accreditation", async () => {
    const jci = await listHospitals({ citySlug: slug("gurugram"), accreditation: "jci" });
    expect(jci.items.map((h) => h.slug)).toEqual([slug("heart-institute")]);

    const none = await listHospitals({ citySlug: slug("chennai"), accreditation: "jci" });
    expect(none.items).toEqual([]);
  });

  test("never contains admin-only data", async () => {
    expectNoPrivateData(await listHospitals());
  });
});
