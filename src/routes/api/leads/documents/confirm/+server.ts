import * as z from "zod";
import { UPLOAD_GRANT_SECRET } from "$app/env/private";
import { requestMeta } from "#lib/server/audit.js";
import { isJsonRequest, jsonReply } from "#lib/server/http.js";
import { confirmDocumentUpload, DocumentError } from "#lib/server/leads/documents.js";
import { verifyUploadGrant } from "#lib/server/leads/upload-grant.js";
import { patientDocumentStore } from "#lib/server/storage/index.js";
import type { RequestHandler } from "./$types";

const confirmSchema = z.object({ documentId: z.uuid() });

/** POST /api/leads/documents/confirm — body { grant, documentId }, after the browser's PUT. */
export const POST: RequestHandler = async (event) => {
  if (!isJsonRequest(event.request)) return jsonReply(415, { error: "unsupported_media_type" });

  const body = await event.request.json().catch(() => null);
  const leadId = verifyUploadGrant(body?.grant, UPLOAD_GRANT_SECRET);
  if (!leadId) return jsonReply(403, { error: "invalid_grant" });

  const parsed = confirmSchema.safeParse(body);
  if (!parsed.success) return jsonReply(400, { error: "invalid" });

  try {
    await confirmDocumentUpload(
      leadId,
      parsed.data.documentId,
      patientDocumentStore(),
      requestMeta(event)
    );
    return jsonReply(200, { ok: true });
  } catch (err) {
    if (err instanceof DocumentError) {
      return jsonReply(err.code === "not_found" ? 404 : 422, {
        error: err.code,
        message: err.message
      });
    }
    throw err;
  }
};
