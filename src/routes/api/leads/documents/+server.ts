import * as z from "zod";
import { UPLOAD_GRANT_SECRET } from "$app/env/private";
import { documentUploadSchema } from "#lib/domain/documents.js";
import { isJsonRequest, jsonReply } from "#lib/server/http.js";
import { DocumentError, requestDocumentUpload } from "#lib/server/leads/documents.js";
import { verifyUploadGrant } from "#lib/server/leads/upload-grant.js";
import { patientDocumentStore } from "#lib/server/storage/index.js";
import type { RequestHandler } from "./$types";

/**
 * POST /api/leads/documents — reserve an upload for the lead in `grant`.
 * Body: { grant, kind, filename, mimeType, size }
 * 201 { documentId, uploadUrl, expiresIn }: the browser then PUTs the file to uploadUrl
 * with header `Content-Type: <mimeType>`, and calls /api/leads/documents/confirm.
 */
export const POST: RequestHandler = async ({ request }) => {
  if (!isJsonRequest(request)) return jsonReply(415, { error: "unsupported_media_type" });

  const body = await request.json().catch(() => null);
  const leadId = verifyUploadGrant(body?.grant, UPLOAD_GRANT_SECRET);
  if (!leadId) return jsonReply(403, { error: "invalid_grant" });

  const parsed = documentUploadSchema.safeParse(body);
  if (!parsed.success) {
    return jsonReply(400, { error: "invalid", fields: z.flattenError(parsed.error).fieldErrors });
  }

  try {
    return jsonReply(201, await requestDocumentUpload(leadId, parsed.data, patientDocumentStore()));
  } catch (err) {
    if (err instanceof DocumentError) {
      return jsonReply(409, { error: err.code, message: err.message });
    }
    throw err;
  }
};
