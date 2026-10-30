import { randomUUID } from "node:crypto";
import { eq } from "drizzle-orm";
import type { ImagePreset } from "#lib/domain/images.js";
import { db } from "../db/index.js";
import { doctors, hospitals } from "../db/schema/index.js";
import { logger } from "../logger.js";
import type { ObjectStore } from "../storage/types.js";
import { toPublicWebp } from "./images.js";

/** Processes and stores an image under a new random key. Keys never change, so caches never go stale. */
async function storeImage(file: File, preset: ImagePreset, store: ObjectStore) {
  const bytes = await toPublicWebp(file, preset);
  const key = `${preset}/${randomUUID()}.webp`;
  await store.put(key, bytes, "image/webp");
  return key;
}

/** Old images are removed after the database points at the new one; a failure only leaves an orphan. */
async function deleteReplaced(store: ObjectStore, key: string | null | undefined) {
  if (!key) return;
  await store.delete(key).catch((err) => logger.warn({ err, key }, "could not delete old image"));
}

const HOSPITAL_SLOTS = {
  logo: { preset: "hospitalLogo", column: "logoKey" },
  cover: { preset: "hospitalCover", column: "coverImageKey" }
} as const;

export async function setHospitalImage(
  hospitalId: string,
  slot: keyof typeof HOSPITAL_SLOTS,
  file: File,
  store: ObjectStore
) {
  const { preset, column } = HOSPITAL_SLOTS[slot];
  const [hospital] = await db
    .select({ previousKey: hospitals[column] })
    .from(hospitals)
    .where(eq(hospitals.id, hospitalId));
  if (!hospital) throw new Error(`hospital ${hospitalId} not found`);

  const key = await storeImage(file, preset, store);
  await db
    .update(hospitals)
    .set({ [column]: key })
    .where(eq(hospitals.id, hospitalId));

  await deleteReplaced(store, hospital.previousKey);
  return key;
}

export async function setDoctorPhoto(doctorId: string, file: File, store: ObjectStore) {
  const [doctor] = await db
    .select({ previousKey: doctors.photoKey })
    .from(doctors)
    .where(eq(doctors.id, doctorId));
  if (!doctor) throw new Error(`doctor ${doctorId} not found`);

  const key = await storeImage(file, "doctorPhoto", store);
  await db.update(doctors).set({ photoKey: key }).where(eq(doctors.id, doctorId));

  await deleteReplaced(store, doctor.previousKey);
  return key;
}
