import { describe, expect, test } from "vitest";
import { verifyTurnstile, type TurnstileCheck } from "./turnstile.js";

/** A fake fetch that answers like Cloudflare's siteverify. */
const siteverify = (body: object, status = 200): typeof fetch =>
  (async () => Response.json(body, { status })) as unknown as typeof fetch;

const production = (fetcher: typeof fetch): TurnstileCheck => ({
  secret: "secret",
  expectedHostname: "medtour.example",
  expectedAction: "lead",
  allowTestingKeys: false,
  fetch: fetcher
});

describe("verifyTurnstile", () => {
  test("accepts a real token for our hostname and action", async () => {
    const fetch = siteverify({ success: true, hostname: "medtour.example", action: "lead" });
    expect(await verifyTurnstile("token", "203.0.113.9", production(fetch))).toEqual({ ok: true });
  });

  test("rejects a token issued for another site or form", async () => {
    const otherSite = siteverify({ success: true, hostname: "evil.example", action: "lead" });
    const otherForm = siteverify({ success: true, hostname: "medtour.example", action: "login" });
    expect(await verifyTurnstile("token", null, production(otherSite))).toMatchObject({
      reason: "mismatch"
    });
    expect(await verifyTurnstile("token", null, production(otherForm))).toMatchObject({
      reason: "mismatch"
    });
  });

  test("rejects Cloudflare test-key results unless explicitly allowed (dev)", async () => {
    const fetch = siteverify({ success: true, metadata: { result_with_testing_key: true } });
    expect(await verifyTurnstile("token", null, production(fetch))).toMatchObject({
      reason: "testing_key"
    });
    expect(
      await verifyTurnstile("token", null, { ...production(fetch), allowTestingKeys: true })
    ).toEqual({ ok: true });
  });

  test("fails closed when Cloudflare says no, errors, or is unreachable", async () => {
    const no = siteverify({ success: false, "error-codes": ["timeout-or-duplicate"] });
    const serverError = siteverify({}, 500);
    const offline = (async () => {
      throw new TypeError("network down");
    }) as unknown as typeof fetch;

    expect(await verifyTurnstile("token", null, production(no))).toMatchObject({
      reason: "rejected"
    });
    expect(await verifyTurnstile("token", null, production(serverError))).toMatchObject({
      reason: "unavailable"
    });
    expect(await verifyTurnstile("token", null, production(offline))).toMatchObject({
      reason: "unavailable"
    });
  });

  test("rejects missing or oversized tokens without calling Cloudflare", async () => {
    const neverCalled = (async () => {
      throw new Error("should not be called");
    }) as unknown as typeof fetch;
    expect(await verifyTurnstile(undefined, null, production(neverCalled))).toMatchObject({
      reason: "missing"
    });
    expect(await verifyTurnstile("x".repeat(2049), null, production(neverCalled))).toMatchObject({
      reason: "missing"
    });
  });
});
