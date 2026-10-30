// Usage: bun scripts/seed.ts — loads the launch cities and specialties. Safe to run again:
// rows are matched by slug and updated, never duplicated.
import { eq, sql } from "drizzle-orm";
import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import { cities, specialties } from "#lib/server/db/schema/index.js";
import { SEED_CITIES, SEED_SPECIALTIES } from "./seed-data.js";

const { DATABASE_URL } = process.env;
if (!DATABASE_URL) {
  console.error("DATABASE_URL is not set");
  process.exit(1);
}

const client = postgres(DATABASE_URL, { max: 1 });
const db = drizzle(client, { casing: "snake_case" });

/** On a slug clash, overwrite these columns with the incoming ("excluded") values. */
const updateFromSeed = (columns: string[]) =>
  Object.fromEntries(columns.map((column) => [column, sql.raw(`excluded.${column}`)]));

try {
  await db.transaction(async (tx) => {
    await tx
      .insert(cities)
      .values(SEED_CITIES.map((city, index) => ({ ...city, sortOrder: index })))
      .onConflictDoUpdate({
        target: cities.slug,
        set: updateFromSeed(["name", "state", "airport_code", "airport_name", "sort_order"])
      });

    // Keep the listed order for display, but insert parents first so children can point at them
    const listed = SEED_SPECIALTIES.map((specialty, sortOrder) => ({ ...specialty, sortOrder }));
    const ordered = [...listed.filter((s) => !s.parent), ...listed.filter((s) => s.parent)];
    for (const { parent, ...specialty } of ordered) {
      const parentId = parent
        ? (
            await tx
              .select({ id: specialties.id })
              .from(specialties)
              .where(eq(specialties.slug, parent))
          )[0]?.id
        : null;
      await tx
        .insert(specialties)
        .values({ ...specialty, parentId })
        .onConflictDoUpdate({
          target: specialties.slug,
          set: updateFromSeed(["name", "icon", "parent_id", "sort_order"])
        });
    }
  });

  console.log(`Seeded ${SEED_CITIES.length} cities and ${SEED_SPECIALTIES.length} specialties`);
} finally {
  await client.end();
}
