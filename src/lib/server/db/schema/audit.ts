import { bigint, index, inet, jsonb, pgTable, text, timestamp, uuid } from "drizzle-orm/pg-core";
import { actorType } from "./enums.js";

/** Append-only (enforced by trigger in migration 0004). Kept ≥ 1 year per DPDP Rule 6. */
export const auditLogs = pgTable(
  "audit_logs",
  {
    id: bigint({ mode: "number" }).primaryKey().generatedAlwaysAsIdentity(),
    occurredAt: timestamp({ withTimezone: true }).notNull().defaultNow(),
    actorType: actorType().notNull(),
    actorId: text(), // better-auth user ids are text
    action: text().notNull(), // e.g. "lead.viewed", "document.downloaded"
    entityType: text(),
    entityId: text(),
    leadId: uuid(), // deliberately no FK: the log must outlive what it describes
    ipAddress: inet(),
    userAgent: text(),
    metadata: jsonb().$type<Record<string, unknown>>().notNull().default({})
  },
  (t) => [index().on(t.occurredAt), index().on(t.leadId), index().on(t.actorId)]
);
