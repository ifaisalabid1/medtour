import { SITE_URL } from "$app/env/private";
import { listSitemapEntries } from "#lib/server/queries/public/sitemap.js";
import type { RequestHandler } from "./$types";

const escapeXml = (text: string) => text.replace(/[<>&'"]/g, (char) => `&#${char.charCodeAt(0)};`);

/** GET /sitemap.xml — every published page, for search engines. */
export const GET: RequestHandler = async () => {
  const urls = (await listSitemapEntries()).map(({ path, lastModified }) => {
    const loc = `<loc>${escapeXml(new URL(path, SITE_URL).href)}</loc>`;
    const lastmod = lastModified
      ? `<lastmod>${lastModified.toISOString().slice(0, 10)}</lastmod>`
      : "";
    return `  <url>${loc}${lastmod}</url>`;
  });

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls.join("\n")}
</urlset>
`;
  return new Response(xml, {
    headers: {
      "content-type": "application/xml; charset=utf-8",
      "cache-control": "public, max-age=3600"
    }
  });
};
