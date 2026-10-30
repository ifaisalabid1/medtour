import { expect, test } from "vitest";
import { createUploadGrant, UPLOAD_GRANT_TTL_SECONDS, verifyUploadGrant } from "./upload-grant.js";

const secret = "test-secret-that-is-at-least-32-characters";
const leadId = "01a18e01-36e0-77b5-949c-000000000001";

test("a grant verifies to the lead it was issued for", () => {
  expect(verifyUploadGrant(createUploadGrant(leadId, secret), secret)).toBe(leadId);
});

test("expired grants are rejected", () => {
  const issuedAt = Date.now() - (UPLOAD_GRANT_TTL_SECONDS + 1) * 1000;
  expect(verifyUploadGrant(createUploadGrant(leadId, secret, issuedAt), secret)).toBeNull();
});

test("tampered, forged or malformed grants are rejected", () => {
  const grant = createUploadGrant(leadId, secret);
  const [, signature] = grant.split(".");
  const otherLead = Buffer.from(
    JSON.stringify({ leadId: "someone-else", exp: 9999999999 })
  ).toString("base64url");

  expect(verifyUploadGrant(`${otherLead}.${signature}`, secret)).toBeNull(); // payload swapped
  expect(verifyUploadGrant(grant, "a-different-secret-of-at-least-32-chars")).toBeNull();
  expect(verifyUploadGrant("not-a-grant", secret)).toBeNull();
  expect(verifyUploadGrant(undefined, secret)).toBeNull();
});
