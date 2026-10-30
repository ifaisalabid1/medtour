import { eq } from "drizzle-orm";
import sharp from "sharp";
import { beforeAll, expect, test } from "vitest";
import { seedDirectory } from "#test/fixtures/directory.js";
import { createMemoryStore } from "#test/fixtures/memory-store.js";
import { db } from "../db/index.js";
import { doctors, hospitals } from "../db/schema/index.js";
import { getHospitalProfile } from "../queries/public/hospitals.js";
import { setDoctorPhoto, setHospitalImage } from "./directory-images.js";

let slug: (name: string) => string;
let hospitalId: string;
let doctorId: string;

async function photo() {
  const bytes = await sharp({
    create: { width: 1200, height: 800, channels: 3, background: "#888" }
  })
    .jpeg()
    .toBuffer();
  return new File([new Uint8Array(bytes)], "photo.jpg", { type: "image/jpeg" });
}

beforeAll(async () => {
  ({ slug } = await seedDirectory("di"));
  const [hospital] = await db
    .select({ id: hospitals.id })
    .from(hospitals)
    .where(eq(hospitals.slug, slug("heart-institute")));
  const [doctor] = await db
    .select({ id: doctors.id })
    .from(doctors)
    .where(eq(doctors.slug, slug("dr-published")));
  hospitalId = hospital!.id;
  doctorId = doctor!.id;
});

test("a hospital cover is stored as WebP and shown by the public profile", async () => {
  const { store, objects } = createMemoryStore();
  const key = await setHospitalImage(hospitalId, "cover", await photo(), store);

  expect(key).toMatch(/^hospitalCover\/[0-9a-f-]{36}\.webp$/);
  expect(objects.get(key)?.type).toBe("image/webp");
  expect((await getHospitalProfile(slug("heart-institute")))?.coverImageKey).toBe(key);
});

test("replacing an image deletes the old object", async () => {
  const { store, objects } = createMemoryStore();
  const first = await setDoctorPhoto(doctorId, await photo(), store);
  const second = await setDoctorPhoto(doctorId, await photo(), store);

  expect(second).not.toBe(first);
  expect(objects.has(first)).toBe(false);
  expect(objects.has(second)).toBe(true);
});

test("an unknown hospital stores nothing", async () => {
  const { store, objects } = createMemoryStore();
  await expect(
    setHospitalImage("01a18e01-0000-7000-8000-000000000000", "logo", await photo(), store)
  ).rejects.toThrow("not found");
  expect(objects.size).toBe(0);
});
