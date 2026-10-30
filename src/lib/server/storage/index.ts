import {
  R2_ACCESS_KEY_ID,
  R2_ENDPOINT,
  R2_PRIVATE_BUCKET,
  R2_SECRET_ACCESS_KEY
} from "$app/env/private";
import { createR2Store } from "./r2.js";
import type { ObjectStore } from "./types.js";

export type { ObjectStore } from "./types.js";

let patientDocuments: ObjectStore | undefined;

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
