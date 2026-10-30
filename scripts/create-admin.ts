// Usage: bun scripts/create-admin.ts admin@example.com "Full Name"
import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import { auditLogs, users } from "#lib/server/db/schema/index.js";

const [rawEmail, rawName] = process.argv.slice(2);
const { DATABASE_URL } = process.env;

if (!rawEmail || !rawName || !DATABASE_URL) {
  console.error('Usage: bun scripts/create-admin.ts <email> "<full name>"  (needs DATABASE_URL)');
  process.exit(1);
}

const email = rawEmail.trim().toLowerCase(); // better-auth stores emails in lowercase
const client = postgres(DATABASE_URL, { max: 1 });
const db = drizzle(client, { casing: "snake_case" });

try {
  const created = await db.transaction(async (tx) => {
    const [user] = await tx
      .insert(users)
      .values({ email, name: rawName.trim(), emailVerified: true, role: "admin" })
      .onConflictDoNothing({ target: users.email })
      .returning({ id: users.id });
    if (!user) return false;

    await tx.insert(auditLogs).values({
      actorType: "system",
      action: "staff.created",
      entityType: "user",
      entityId: user.id,
      metadata: { role: "admin", via: "cli" }
    });
    return true;
  });

  if (created) {
    console.log(`Admin created: ${email}`);
  } else {
    console.error(`A user with email ${email} already exists`);
    process.exitCode = 1;
  }
} finally {
  await client.end();
}
