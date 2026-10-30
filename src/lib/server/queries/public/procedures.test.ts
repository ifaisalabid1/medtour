import { beforeAll, describe, expect, test } from "vitest";
import { expectNoPrivateData, seedDirectory } from "#test/fixtures/directory.js";
import { getProcedureGuide, listProcedures } from "./procedures.js";

let slug: (name: string) => string;

beforeAll(async () => {
  ({ slug } = await seedDirectory("pp"));
});

describe("getProcedureGuide", () => {
  test("returns logistics, review attribution, hospitals and doctors", async () => {
    const guide = await getProcedureGuide(slug("cabg"));

    expect(guide).toMatchObject({
      name: "CABG",
      logistics: { hospitalStayDays: { min: 5, max: 7 } },
      inclusions: ["Pre-operative tests"],
      costFactors: ["Room category"],
      review: {
        lastReviewedOn: "2026-10-01",
        reviewer: { slug: slug("dr-reviewer"), registrationNumber: "NMC-REV-1" }
      },
      hospitals: [{ slug: slug("heart-institute"), technologies: ["Da Vinci"] }],
      doctors: [{ slug: slug("dr-published") }]
    });
    expect(guide).not.toHaveProperty("id");
  });

  test("never contains admin-only data (tariffs, fees, MOU terms)", async () => {
    expectNoPrivateData(await getProcedureGuide(slug("cabg")));
  });

  test("returns null for draft procedures", async () => {
    expect(await getProcedureGuide(slug("draft-procedure"))).toBeNull();
  });
});

describe("listProcedures", () => {
  test("lists published procedures for a specialty", async () => {
    const items = await listProcedures(slug("cardiology"));
    expect(items.map((p) => p.slug)).toEqual([slug("cabg")]);
  });

  test("never contains admin-only data", async () => {
    expectNoPrivateData(await listProcedures());
  });
});
