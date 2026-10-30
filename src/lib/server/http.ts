/** A JSON response that is never cached: API answers are per-visitor. */
export const jsonReply = (status: number, body: unknown, headers: Record<string, string> = {}) =>
  Response.json(body, { status, headers: { "cache-control": "no-store", ...headers } });

/**
 * JSON only: a browser can't send it to another site without a CORS preflight, which we
 * never allow. That makes cross-site request forgery against these endpoints impossible.
 */
export const isJsonRequest = (request: Request) =>
  request.headers.get("content-type")?.startsWith("application/json") ?? false;
