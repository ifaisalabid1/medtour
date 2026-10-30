const SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify";

interface SiteverifyResult {
  success: boolean;
  hostname?: string;
  action?: string;
  "error-codes"?: string[];
  metadata?: { result_with_testing_key?: boolean };
}

export interface TurnstileCheck {
  secret: string;
  expectedHostname: string;
  expectedAction: string;
  /** Cloudflare's test keys pass any dummy token: allow them in development only. */
  allowTestingKeys: boolean;
  fetch?: typeof fetch;
}

export type TurnstileOutcome =
  | { ok: true }
  | { ok: false; reason: "missing" | "rejected" | "mismatch" | "testing_key" | "unavailable" };

/** Verifies a Turnstile token with Cloudflare. Fails closed: any doubt means "not human". */
export async function verifyTurnstile(
  token: unknown,
  remoteIp: string | null | undefined,
  check: TurnstileCheck
): Promise<TurnstileOutcome> {
  if (typeof token !== "string" || token.length === 0 || token.length > 2048) {
    return { ok: false, reason: "missing" };
  }

  let result: SiteverifyResult;
  try {
    const response = await (check.fetch ?? fetch)(SITEVERIFY_URL, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        secret: check.secret,
        response: token,
        remoteip: remoteIp ?? undefined
      }),
      signal: AbortSignal.timeout(10_000)
    });
    if (!response.ok) return { ok: false, reason: "unavailable" };
    result = (await response.json()) as SiteverifyResult;
  } catch {
    return { ok: false, reason: "unavailable" };
  }

  if (!result.success) return { ok: false, reason: "rejected" };

  if (result.metadata?.result_with_testing_key) {
    return check.allowTestingKeys ? { ok: true } : { ok: false, reason: "testing_key" };
  }
  if (result.hostname !== check.expectedHostname || result.action !== check.expectedAction) {
    return { ok: false, reason: "mismatch" };
  }
  return { ok: true };
}
