import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import { DATABASE_URL } from "$app/env/private";
import * as schema from "./schema/index.js";

const client = postgres(DATABASE_URL, {
  max: 10,
  idle_timeout: 20,
  connect_timeout: 10
});

export const db = drizzle(client, { schema, casing: "snake_case" });

// adapter-bun emits this after in-flight requests finish on SIGINT/SIGTERM
process.on("sveltekit:shutdown", () => client.end({ timeout: 5 }));
