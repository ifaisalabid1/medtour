import { SITE_URL } from "$app/env/private";
import type { RequestHandler } from "./$types";

/** GET /robots.txt — public pages are crawlable; the admin and APIs are not. */
export const GET: RequestHandler = () =>
  new Response(
    `User-agent: *
Allow: /
Disallow: /admin
Disallow: /api/

Sitemap: ${new URL("/sitemap.xml", SITE_URL).href}
`,
    {
      headers: {
        "content-type": "text/plain; charset=utf-8",
        "cache-control": "public, max-age=86400"
      }
    }
  );
