import * as z from "zod";
import { dev } from "$app/env";
import { SITE_URL, TURNSTILE_SECRET_KEY } from "$app/env/private";
import { leadFormSchema } from "#lib/domain/lead-form.js";
import { formatLeadRef } from "#lib/domain/leads.js";
import { requestMeta } from "#lib/server/audit.js";
import { createLead } from "#lib/server/leads/create-lead.js";
import { notifyLeadCreated } from "#lib/server/leads/notify.js";
import { logger } from "#lib/server/logger.js";
import { consumeOrRetryAfter, leadSubmissionLimiter } from "#lib/server/rate-limit.js";
import { verifyTurnstile } from "#lib/server/turnstile.js";
import type { RequestHandler } from "./$types";

const noStore = { "cache-control": "no-store" };
const reply = (status: number, body: unknown, headers: Record<string, string> = {}) =>
  Response.json(body, { status, headers: { ...noStore, ...headers } });

/**
 * POST /api/leads — the enquiry form.
 * 201 { ref }  ·  400 { error: "invalid", fields }  ·  403 verification  ·  415  ·  429
 */
export const POST: RequestHandler = async (event) => {
  // JSON only: browsers can't send it cross-site without a CORS preflight, which we never allow
  if (!event.request.headers.get("content-type")?.startsWith("application/json")) {
    return reply(415, { error: "unsupported_media_type" });
  }

  const meta = requestMeta(event);
  const retryAfter = await consumeOrRetryAfter(leadSubmissionLimiter, meta.ipAddress ?? "unknown");
  if (retryAfter !== null) {
    return reply(429, { error: "rate_limited" }, { "retry-after": String(retryAfter) });
  }

  let body: { turnstileToken?: unknown } & Record<string, unknown>;
  try {
    body = await event.request.json();
  } catch {
    return reply(400, { error: "invalid_json" });
  }

  // Validate before Turnstile: a token is single-use, so don't spend it on a form with typos
  const parsed = leadFormSchema.safeParse(body);
  if (!parsed.success) {
    return reply(400, { error: "invalid", fields: z.flattenError(parsed.error).fieldErrors });
  }

  const human = await verifyTurnstile(body.turnstileToken, meta.ipAddress, {
    secret: TURNSTILE_SECRET_KEY,
    expectedHostname: new URL(SITE_URL).hostname,
    expectedAction: "lead",
    allowTestingKeys: dev
  });
  if (!human.ok) {
    logger.warn({ reason: human.reason }, "lead rejected by Turnstile");
    return reply(403, { error: "verification_failed" });
  }

  const lead = await createLead(parsed.data, meta);
  await notifyLeadCreated(lead, parsed.data);

  return reply(201, { ref: formatLeadRef(lead.refNo) });
};
