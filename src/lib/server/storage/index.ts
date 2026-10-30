import {
  R2_ACCESS_KEY_ID,
  R2_ENDPOINT,
  R2_PRIVATE_BUCKET,
  R2_SECRET_ACCESS_KEY,
  R2_PUBLIC_BUCKET
} from "$app/env/private";
import { createR2Store } from "./r2.js";
import type { ObjectStore } from "./types.js";

export type { ObjectStore } from "./types.js";

let patientDocuments: ObjectStore | undefined;
let publicMedia: ObjectStore | undefined;

/** Private bucket for patient files. Never public; every read goes through a short signed URL. */
export function patientDocumentStore(): ObjectStore {
  patientDocuments ??= createR2Store({
    endpoint: R2_ENDPOINT,
    accessKeyId: R2_ACCESS_KEY_ID,
    secretAccessKey: R2_SECRET_ACCESS_KEY,
    bucket: R2_PRIVATE_BUCKET
  });
  return patientDocuments;
}

/** Public bucket for hospital and doctor photos, served through PUBLIC_MEDIA_URL. */
export function publicMediaStore(): ObjectStore {
  publicMedia ??= createR2Store({
    endpoint: R2_ENDPOINT,
    accessKeyId: R2_ACCESS_KEY_ID,
    secretAccessKey: R2_SECRET_ACCESS_KEY,
    bucket: R2_PUBLIC_BUCKET
  });
  return publicMedia;
}
