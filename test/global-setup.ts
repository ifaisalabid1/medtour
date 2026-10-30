import { drizzle } from "drizzle-orm/postgres-js";
import { migrate } from "drizzle-orm/postgres-js/migrator";
import postgres from "postgres";
import { loadEnv } from "vite";

// Printed before throwing: Vitest's stack-trace mapping can hide errors thrown from globalSetup
function fail(message: string): never {
  console.error(`\n✖ ${message}\n`);
  throw new Error(message);
}

/** Recreates the test database from migrations before every test run. */
export default async function setup() {
  // The same files SvelteKit reads in test mode: .env, overridden by .env.test.local
  const { DATABASE_URL } = loadEnv("test", process.cwd(), "");
  if (!DATABASE_URL) fail("DATABASE_URL is not set");

  const testDb = new URL(DATABASE_URL);
  const testDbName = testDb.pathname.slice(1);
  if (!testDbName.endsWith("_test")) {
    fail(`Refusing to reset "${testDbName}": create .env.test.local with a *_test database`);
  }

  // Drop/create from the built-in `postgres` maintenance database
  const maintenance = new URL(DATABASE_URL);
  maintenance.pathname = "/postgres";
  const admin = postgres(maintenance.href, { max: 1, onnotice: () => {} });
  await admin.unsafe(`drop database if exists "${testDbName}" with (force)`);
  await admin.unsafe(`create database "${testDbName}"`);
  await admin.end();

  const client = postgres(testDb.href, { max: 1, onnotice: () => {} });
  await migrate(drizzle(client), { migrationsFolder: "./drizzle" });
  await client.end();
}
