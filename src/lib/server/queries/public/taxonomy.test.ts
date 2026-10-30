import { beforeAll, describe, expect, test } from "vitest";
import { seedDirectory } from "#test/fixtures/directory.js";
import { getCity, getSpecialty, listCities, listSpecialties } from "./taxonomy.js";

let slug: (name: string) => string;

beforeAll(async () => {
  ({ slug } = await seedDirectory("pt"));
});

describe("cities", () => {
  test("lists cities with their count of published hospitals", async () => {
    const mine = (await listCities()).filter((c) => c.slug.startsWith("pt-"));
    expect(mine).toEqual([
      { slug: slug("chennai"), name: "Chennai", state: "Tamil Nadu", hospitalCount: 1 },
      { slug: slug("gurugram"), name: "Gurugram", state: "Haryana", hospitalCount: 1 }
    ]);
  });

  test("gets one city by slug", async () => {
    expect(await getCity(slug("gurugram"))).toMatchObject({ name: "Gurugram", airportCode: "DEL" });
    expect(await getCity("pt-nowhere")).toBeNull();
  });
});

describe("specialties", () => {
  test("lists specialties with their parent", async () => {
    const mine = (await listSpecialties()).filter((s) => s.slug.startsWith("pt-"));
    expect(mine.find((s) => s.slug === slug("cardiac-surgery"))?.parentSlug).toBe(
      slug("cardiology")
    );
    expect(mine.find((s) => s.slug === slug("cardiology"))?.parentSlug).toBeNull();
  });

  test("gets one specialty by slug", async () => {
    expect(await getSpecialty(slug("oncology"))).toMatchObject({ name: "Oncology" });
  });
});
