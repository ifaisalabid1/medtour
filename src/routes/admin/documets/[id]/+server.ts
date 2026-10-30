import { error, redirect } from "@sveltejs/kit";
import * as z from "zod";
import { requestMeta } from "#lib/server/audit.js";
import { createDocumentDownloadUrl, DocumentError } from "#lib/server/leads/documents.js";
import { patientDocumentStore } from "#lib/server/storage/index.js";
import type { RequestHandler } from "./$types";

/** GET /admin/documents/:id — audited, 10-minute redirect to a patient file (staff only). */
export const GET: RequestHandler = async (event) => {
  // hooks.server.ts already guards /admin; checked again here because this serves patient data
  const user = event.locals.user;
  if (!user) error(401, "Sign in required");

  const id = z.uuid().safeParse(event.params.id);
  if (!id.success) error(404, "Document not found");

  let url: string;
  try {
    url = await createDocumentDownloadUrl(
      id.data,
      user.id,
      patientDocumentStore(),
      requestMeta(event)
    );
  } catch (err) {
    if (err instanceof DocumentError) error(404, "Document not found");
    throw err;
  }
  redirect(303, url, { external: true });
};
