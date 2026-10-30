import { eq } from "drizzle-orm";
import { beforeAll, describe, expect, test } from "vitest";
import { createMemoryStore } from "#test/fixtures/memory-store.js";
import { MAX_DOCUMENTS_PER_LEAD, type DocumentUpload } from "#lib/domain/documents.js";
import { db } from "../db/index.js";
import { auditLogs, patientDocuments, patientLeads, users } from "../db/schema/index.js";
import {
  confirmDocumentUpload,
  createDocumentDownloadUrl,
  DocumentError,
  requestDocumentUpload
} from "./documents.js";

const PDF = "%PDF-1.4\n%%EOF\n";
const request = { ipAddress: "203.0.113.9", userAgent: "DocTest/1.0" };
const pdfUpload = (size = PDF.length): DocumentUpload => ({
  kind: "medical_report",
  filename: "echo report.pdf",
  mimeType: "application/pdf",
  size
});

let leadId: string; // upload tests (fills up to the per-lead limit)
let downloadLeadId: string; // download tests
let staffId: string;

const newLead = async (email: string) => {
  const [lead] = await db
    .insert(patientLeads)
    .values({
      fullName: "Doc Test",
      email,
      phone: "+2348012345678",
      description: "Needs a second opinion.",
      countryCode: "NG",
      passportCountry: "NG",
      intent: "second_opinion"
    })
    .returning();
  return lead!.id;
};

beforeAll(async () => {
  leadId = await newLead("doc-test@example.com");
  downloadLeadId = await newLead("doc-download@example.com");
  const [staff] = await db
    .insert(users)
    .values({ name: "Case Manager", email: "doc-test-staff@example.com", emailVerified: true })
    .returning();
  staffId = staff!.id;
});

const keyOf = async (documentId: string) =>
  (await db.select().from(patientDocuments).where(eq(patientDocuments.id, documentId)))[0]
    ?.objectKey;

describe("patient document upload", () => {
  test("reserve → direct upload → confirm marks the document uploaded and audits it", async () => {
    const { store, put } = createMemoryStore();
    const { documentId, uploadUrl } = await requestDocumentUpload(leadId, pdfUpload(), store);
    expect(uploadUrl).toContain("type=application/pdf");

    const key = await keyOf(documentId);
    expect(key).toMatch(new RegExp(`^leads/${leadId}/[0-9a-f-]{36}\\.pdf$`)); // not the filename
    put(key!, PDF, "application/pdf");

    await confirmDocumentUpload(leadId, documentId, store, request);

    const [saved] = await db
      .select()
      .from(patientDocuments)
      .where(eq(patientDocuments.id, documentId));
    expect(saved?.uploadedAt).toBeInstanceOf(Date);
    const audit = await db.select().from(auditLogs).where(eq(auditLogs.entityId, documentId));
    expect(audit).toMatchObject([{ action: "document.uploaded", actorType: "patient", leadId }]);
  });

  test("a file that is not what it claims is deleted, with its row", async () => {
    const { store, put, objects } = createMemoryStore();
    const fakePdf = "\x89PNG\r\n\x1a\n-------";
    const { documentId } = await requestDocumentUpload(leadId, pdfUpload(fakePdf.length), store);
    const key = (await keyOf(documentId))!;
    put(key, fakePdf, "application/pdf");

    await expect(confirmDocumentUpload(leadId, documentId, store, request)).rejects.toMatchObject({
      code: "upload_invalid"
    });
    expect(objects.has(key)).toBe(false);
    expect(await keyOf(documentId)).toBeUndefined();
  });

  test("a file larger than announced is rejected", async () => {
    const { store, put } = createMemoryStore();
    const { documentId } = await requestDocumentUpload(leadId, pdfUpload(5), store);
    put((await keyOf(documentId))!, PDF, "application/pdf");

    await expect(confirmDocumentUpload(leadId, documentId, store, request)).rejects.toMatchObject({
      code: "upload_invalid"
    });
  });

  test("another lead's grant cannot confirm this lead's document", async () => {
    const { store } = createMemoryStore();
    const { documentId } = await requestDocumentUpload(leadId, pdfUpload(), store);
    const otherLead = "01a18e01-0000-7000-8000-000000000000";

    await expect(
      confirmDocumentUpload(otherLead, documentId, store, request)
    ).rejects.toMatchObject({
      code: "not_found"
    });
  });

  test(`stops at ${MAX_DOCUMENTS_PER_LEAD} files per lead`, async () => {
    const { store } = createMemoryStore();
    const existing = await db.$count(patientDocuments, eq(patientDocuments.leadId, leadId));
    for (let i = existing; i < MAX_DOCUMENTS_PER_LEAD; i++) {
      await requestDocumentUpload(leadId, pdfUpload(), store);
    }
    await expect(requestDocumentUpload(leadId, pdfUpload(), store)).rejects.toBeInstanceOf(
      DocumentError
    );
  });
});

describe("staff download", () => {
  test("audits the download, then returns a short-lived link", async () => {
    const { store } = createMemoryStore();
    const { documentId } = await requestDocumentUpload(downloadLeadId, pdfUpload(), store);
    await db
      .update(patientDocuments)
      .set({ uploadedAt: new Date() })
      .where(eq(patientDocuments.id, documentId));

    const url = await createDocumentDownloadUrl(documentId, staffId, store, request);
    expect(url).toContain("ttl=600");

    const audit = await db.select().from(auditLogs).where(eq(auditLogs.entityId, documentId));
    expect(audit).toMatchObject([
      {
        action: "document.downloaded",
        actorType: "staff",
        actorId: staffId,
        leadId: downloadLeadId
      }
    ]);
  });

  test("documents that were never uploaded cannot be downloaded", async () => {
    const { store } = createMemoryStore();
    const { documentId } = await requestDocumentUpload(downloadLeadId, pdfUpload(), store);

    await expect(
      createDocumentDownloadUrl(documentId, staffId, store, request)
    ).rejects.toMatchObject({
      code: "not_found"
    });
  });
});
