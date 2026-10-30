import { createHmac, timingSafeEqual } from "node:crypto";

// A patient has no account, so after they submit an enquiry we hand them a short-lived,
// signed "grant" that allows uploading files to that one lead and nothing else.

export const UPLOAD_GRANT_TTL_SECONDS = 2 * 60 * 60; // 2 hours

const sign = (payload: string, secret: string) =>
  createHmac("sha256", secret).update(payload).digest("base64url");

export function createUploadGrant(leadId: string, secret: string, now = Date.now()): string {
  const payload = Buffer.from(
    JSON.stringify({ leadId, exp: Math.floor(now / 1000) + UPLOAD_GRANT_TTL_SECONDS })
  ).toString("base64url");
  return `${payload}.${sign(payload, secret)}`;
}

/** The lead id the grant was issued for, or null if it is forged, tampered with or expired. */
export function verifyUploadGrant(grant: unknown, secret: string, now = Date.now()): string | null {
  if (typeof grant !== "string" || grant.length > 512) return null;
  const [payload, signature] = grant.split(".");
  if (!payload || !signature) return null;

  const expected = Buffer.from(sign(payload, secret));
  const actual = Buffer.from(signature);
  if (actual.length !== expected.length || !timingSafeEqual(actual, expected)) return null;

  try {
    const { leadId, exp } = JSON.parse(Buffer.from(payload, "base64url").toString("utf8"));
    if (typeof leadId !== "string" || typeof exp !== "number") return null;
    return exp > Math.floor(now / 1000) ? leadId : null;
  } catch {
    return null;
  }
}
