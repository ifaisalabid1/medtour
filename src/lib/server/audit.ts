import { isIP } from "node:net";
import type { RequestEvent } from "@sveltejs/kit";
import type { ActorType } from "#lib/domain/audit.js";
import { db } from "./db/index.js";
import { auditLogs } from "./db/schema/index.js";

/** Every audited action. Add new ones here; no migration needed. */
export type AuditAction =
  | "staff.created"
  | "auth.sign_in"
  | "auth.sign_in_failed"
  | "auth.sign_out"
  | "auth.session_revoked"
  | "lead.created"
  | "lead.viewed"
  | "lead.updated"
  | "lead.anonymized"
  | "consent.granted"
  | "consent.withdrawn"
  | "document.uploaded"
  | "document.downloaded"
  | "document.deleted"
  | "tariff.viewed"
  | "tariff.updated";

export interface AuditEntry {
  actorType: ActorType;
  actorId?: string | null;
  action: AuditAction;
  entityType?: string;
  entityId?: string;
  leadId?: string;
  ipAddress?: string | null;
  userAgent?: string | null;
  metadata?: Record<string, unknown>;
}

/** The app-wide `db` or a transaction, so an audit row can commit together with the change it records. */
type Executor = Pick<typeof db, "insert">;

/**
 * Writes an audit row. Awaited and allowed to throw on purpose: under DPDP an action on
 * personal data that can't be logged must not happen silently.
 */
export async function recordAudit(entry: AuditEntry, executor: Executor = db): Promise<void> {
  await executor.insert(auditLogs).values(entry);
}

/** Client IP and user agent of the current request, for AuditEntry. */
export function requestMeta(event: RequestEvent): Pick<AuditEntry, "ipAddress" | "userAgent"> {
  let ip: string | null = null;
  try {
    ip = event.getClientAddress();
  } catch {
    // no address available (e.g. during prerendering)
  }
  return {
    ipAddress: ip && isIP(ip) ? ip : null, // the column is `inet`: never let a bad value fail the insert
    userAgent: event.request.headers.get("user-agent")
  };
}
