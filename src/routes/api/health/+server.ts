import { sql } from "drizzle-orm";
import { db } from "#lib/server/db/index.js";
import { logger } from "#lib/server/logger.js";
import type { RequestHandler } from "./$types";

const headers = { "cache-control": "no-store" };

export const GET: RequestHandler = async () => {
  try {
    await db.execute(sql`select 1`);
    return Response.json({ status: "ok" }, { headers });
  } catch (err) {
    logger.error({ err }, "health check failed: database unreachable");
    return Response.json({ status: "error" }, { status: 503, headers });
  }
};
