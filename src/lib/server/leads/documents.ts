import { randomUUID } from "node:crypto";
import { and, eq, isNotNull } from "drizzle-orm";
import {
  DOCUMENT_TYPES,
  MAX_DOCUMENT_BYTES,
  MAX_DOCUMENTS_PER_LEAD,
  type DocumentUpload
} from "#lib/domain/documents.js";
import { recordAudit, type AuditEntry } from "../audit.js";
import { db } from "../db/index.js";
import { patientDocuments } from "../db/schema/index.js";
import type { ObjectStore } from "../storage/types.js";

const UPLOAD_URL_TTL = 10 * 60; // the browser must start the upload within 10 minutes
const DOWNLOAD_URL_TTL = 10 * 60; // staff links stop working after 10 minutes

type RequestInfo = Pick<AuditEntry, "ipAddress" | "userAgent">;

export class DocumentError extends Error {
  constructor(
    readonly code: "limit_reached" | "not_found" | "upload_missing" | "upload_invalid",
    message: string
  ) {
    super(message);
  }
}

/** Reserves a document slot and returns a URL the patient's browser uploads to directly. */
export async function requestDocumentUpload(
  leadId: string,
  upload: DocumentUpload,
  store: ObjectStore
) {
  const existing = await db.$count(patientDocuments, eq(patientDocuments.leadId, leadId));
  if (existing >= MAX_DOCUMENTS_PER_LEAD) {
    throw new DocumentError(
      "limit_reached",
      `You can upload up to ${MAX_DOCUMENTS_PER_LEAD} files`
    );
  }

  // Random key: never derived from the filename, which the patient controls
  const objectKey = `leads/${leadId}/${randomUUID()}.${DOCUMENT_TYPES[upload.mimeType]}`;
  const [document] = await db
    .insert(patientDocuments)
    .values({
      leadId,
      kind: upload.kind,
      objectKey,
      originalFilename: upload.filename,
      mimeType: upload.mimeType,
      sizeBytes: upload.size
    })
    .returning({ id: patientDocuments.id });

  return {
    documentId: document!.id,
    uploadUrl: store.presignUpload(objectKey, { type: upload.mimeType, expiresIn: UPLOAD_URL_TTL }),
    expiresIn: UPLOAD_URL_TTL
  };
}

/** Leading bytes ("magic numbers") of each allowed type: the file must really be what it claims. */
function matchesType(bytes: Uint8Array, mimeType: string): boolean {
  const ascii = (start: number, end: number) => String.fromCharCode(...bytes.slice(start, end));
  switch (mimeType) {
    case "application/pdf":
      return ascii(0, 5) === "%PDF-";
    case "image/jpeg":
      return bytes[0] === 0xff && bytes[1] === 0xd8 && bytes[2] === 0xff;
    case "image/png":
      return ascii(1, 4) === "PNG" && bytes[0] === 0x89;
    case "image/webp":
      return ascii(0, 4) === "RIFF" && ascii(8, 12) === "WEBP";
    case "image/heic":
      return ascii(4, 8) === "ftyp";
    default:
      return false;
  }
}

/**
 * Called after the browser's upload finishes. Checks the stored object really is the file that
 * was announced; anything else is deleted. Only then does the document count as uploaded.
 */
export async function confirmDocumentUpload(
  leadId: string,
  documentId: string,
  store: ObjectStore,
  request: RequestInfo
) {
  const [document] = await db
    .select()
    .from(patientDocuments)
    .where(and(eq(patientDocuments.id, documentId), eq(patientDocuments.leadId, leadId)));
  if (!document) throw new DocumentError("not_found", "Document not found");
  if (document.uploadedAt) return; // already confirmed: confirming twice is harmless

  const stored = await store.stat(document.objectKey);
  if (!stored) throw new DocumentError("upload_missing", "The upload has not finished");

  const valid =
    stored.size === document.sizeBytes &&
    stored.size <= MAX_DOCUMENT_BYTES &&
    matchesType(await store.readStart(document.objectKey, 12), document.mimeType);

  if (!valid) {
    await store.delete(document.objectKey);
    await db.delete(patientDocuments).where(eq(patientDocuments.id, documentId));
    throw new DocumentError("upload_invalid", "The file does not match what was announced");
  }

  await db.transaction(async (tx) => {
    await tx
      .update(patientDocuments)
      .set({ uploadedAt: new Date() })
      .where(eq(patientDocuments.id, documentId));
    await recordAudit(
      {
        actorType: "patient",
        action: "document.uploaded",
        entityType: "document",
        entityId: documentId,
        leadId,
        metadata: { kind: document.kind, sizeBytes: stored.size },
        ...request
      },
      tx
    );
  });
}

/**
 * A 10-minute download link for staff. The audit row is written first: if it can't be
 * recorded, no link is issued (DPDP Rule 6 access logging).
 */
export async function createDocumentDownloadUrl(
  documentId: string,
  staffUserId: string,
  store: ObjectStore,
  request: RequestInfo
) {
  const [document] = await db
    .select({
      leadId: patientDocuments.leadId,
      objectKey: patientDocuments.objectKey,
      originalFilename: patientDocuments.originalFilename
    })
    .from(patientDocuments)
    .where(and(eq(patientDocuments.id, documentId), isNotNull(patientDocuments.uploadedAt)));
  if (!document) throw new DocumentError("not_found", "Document not found");

  await recordAudit({
    actorType: "staff",
    actorId: staffUserId,
    action: "document.downloaded",
    entityType: "document",
    entityId: documentId,
    leadId: document.leadId,
    ...request
  });

  return store.presignDownload(document.objectKey, {
    filename: document.originalFilename,
    expiresIn: DOWNLOAD_URL_TTL
  });
}
