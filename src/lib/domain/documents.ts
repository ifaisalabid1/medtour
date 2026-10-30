import * as z from "zod";
import { DOCUMENT_KINDS } from "./leads.js";

/** File types patients may upload, with the extension used for the stored object. */
export const DOCUMENT_TYPES = {
  "application/pdf": "pdf",
  "image/jpeg": "jpg",
  "image/png": "png",
  "image/webp": "webp",
  "image/heic": "heic"
} as const;
export type DocumentMimeType = keyof typeof DOCUMENT_TYPES;

export const MAX_DOCUMENT_BYTES = 20 * 1024 * 1024; // 20 MB: enough for scanned reports
export const MAX_DOCUMENTS_PER_LEAD = 10;

export const documentUploadSchema = z.object({
  kind: z.enum(DOCUMENT_KINDS),
  filename: z.string().trim().min(1).max(200),
  mimeType: z.enum(
    Object.keys(DOCUMENT_TYPES) as [DocumentMimeType, ...DocumentMimeType[]],
    "Upload a PDF, JPG, PNG, WebP or HEIC file"
  ),
  size: z.int().min(1).max(MAX_DOCUMENT_BYTES, "Files must be 20 MB or smaller")
});
export type DocumentUpload = z.output<typeof documentUploadSchema>;
