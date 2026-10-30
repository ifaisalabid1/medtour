import { beforeAll, expect, test } from "vitest";
import { seedDirectory } from "#test/fixtures/directory.js";
import { paths } from "#lib/paths.js";
import { listSitemapEntries } from "./sitemap.js";

let slug: (name: string) => string;
let sitemap: string[];

beforeAll(async () => {
  ({ slug } = await seedDirectory("sm"));
  sitemap = (await listSitemapEntries()).map((entry) => entry.path);
});

test("lists published profiles and guides", () => {
  expect(sitemap).toContain(paths.hospital(slug("heart-institute")));
  expect(sitemap).toContain(paths.doctor(slug("dr-published")));
  expect(sitemap).toContain(paths.treatment(slug("cabg")));
});

test("lists listing pages that have results", () => {
  expect(sitemap).toContain(paths.hospitalsInCity(slug("gurugram")));
  expect(sitemap).toContain(paths.hospitalsBySpecialtyInCity(slug("cardiology"), slug("gurugram")));
  expect(sitemap).toContain(paths.doctorsBySpecialtyInCity(slug("oncology"), slug("chennai")));
  expect(sitemap).toContain(paths.specialty(slug("cardiology")));
});

test("leaves out drafts and empty combinations", () => {
  expect(sitemap).not.toContain(paths.hospital(slug("draft-hospital")));
  expect(sitemap).not.toContain(paths.doctor(slug("dr-draft")));
  expect(sitemap).not.toContain(paths.treatment(slug("draft-procedure")));
  // No oncology hospital in Gurugram, and Cardiac Surgery has no content at all
  expect(sitemap).not.toContain(
    paths.hospitalsBySpecialtyInCity(slug("oncology"), slug("gurugram"))
  );
  expect(sitemap).not.toContain(paths.specialty(slug("cardiac-surgery")));
});

test("has no duplicate URLs", () => {
  expect(new Set(sitemap).size).toBe(sitemap.length);
});

test("dates come from the record's last update", async () => {
  const entry = (await listSitemapEntries()).find(
    (e) => e.path === paths.hospital(slug("heart-institute"))
  );
  expect(entry?.lastModified).toBeInstanceOf(Date);
});
