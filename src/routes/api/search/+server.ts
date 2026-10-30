import { searchDirectory } from "#lib/server/queries/public/search.js";
import type { RequestHandler } from "./$types";

/** GET /api/search?q=… — instant search for the header search box. */
export const GET: RequestHandler = async ({ url }) => {
  const results = await searchDirectory(url.searchParams.get("q") ?? "");
  // Public data only, so browsers and Cloudflare may cache each query for a minute
  return Response.json({ results }, { headers: { "cache-control": "public, max-age=60" } });
};
