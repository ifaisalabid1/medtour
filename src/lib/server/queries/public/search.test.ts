import { beforeAll, expect, test } from "vitest";
import { expectNoPrivateData, seedDirectory } from "#test/fixtures/directory.js";
import { searchDirectory } from "./search.js";

let slug: (name: string) => string;

// Other test files seed rows with the same names, so search wide and look for ours
const find = async (query: string) => (await searchDirectory(query, 50)).map((r) => r.slug);

beforeAll(async () => {
  ({ slug } = await seedDirectory("ps"));
});

test("finds specialties, hospitals, doctors and procedures by name", async () => {
  expect(await find("Oncology")).toContain(slug("oncology"));
  expect(await find("Heart Institute")).toContain(slug("heart-institute"));
  expect(await find("Dr Oncologist")).toContain(slug("dr-oncologist"));
  expect(await find("CABG")).toContain(slug("cabg"));
});

test("tolerates typos", async () => {
  expect(await find("hart institut")).toContain(slug("heart-institute"));
  expect(await find("oncologst")).toContain(slug("dr-oncologist"));
  expect(await find("cardiolgy")).toContain(slug("cardiology"));
});

test("returns what the UI needs: type, title and a subtitle", async () => {
  const [hospital] = (await searchDirectory("Heart Institute", 50)).filter(
    (r) => r.slug === slug("heart-institute")
  );
  expect(hospital).toEqual({
    type: "hospital",
    slug: slug("heart-institute"),
    title: "Heart Institute",
    subtitle: "Gurugram"
  });
});

test("never finds drafts", async () => {
  expect(await find("Draft Hospital")).not.toContain(slug("draft-hospital"));
  expect(await find("Dr Draft")).not.toContain(slug("dr-draft"));
  expect(await find("Draft Procedure")).not.toContain(slug("draft-procedure"));
});

test("ignores queries that are too short and survives search syntax", async () => {
  expect(await searchDirectory("a")).toEqual([]);
  expect(await searchDirectory('"unclosed quote -or OR & | !')).toBeInstanceOf(Array);
});

test("never searches or returns admin-only data", async () => {
  expect(await searchDirectory("SENTINEL")).toEqual([]);
  expectNoPrivateData(await searchDirectory("Heart", 50));
});
