import type { RequestEvent } from "@sveltejs/kit";
import { eq } from "drizzle-orm";
import { describe, expect, test } from "vitest";
import { recordAudit, requestMeta } from "./audit.js";
import { db } from "./db/index.js";
import { auditLogs } from "./db/schema/index.js";

function fakeEvent(ip: string, userAgent: string): RequestEvent {
  return {
    getClientAddress: () => ip,
    request: new Request("http://localhost/", { headers: { "user-agent": userAgent } })
  } as unknown as RequestEvent;
}

describe("requestMeta", () => {
  test("keeps a valid IP and the user agent", () => {
    expect(requestMeta(fakeEvent("203.0.113.7", "Browser/1.0"))).toEqual({
      ipAddress: "203.0.113.7",
      userAgent: "Browser/1.0"
    });
  });

  test("drops an invalid IP instead of failing the insert", () => {
    expect(requestMeta(fakeEvent("not-an-ip", "Browser/1.0")).ipAddress).toBeNull();
  });
});

describe("recordAudit", () => {
  test("writes a row", async () => {
    await recordAudit({ actorType: "system", action: "lead.viewed", entityId: "test-write" });

    const rows = await db.select().from(auditLogs).where(eq(auditLogs.entityId, "test-write"));
    expect(rows).toHaveLength(1);
    expect(rows[0]).toMatchObject({ actorType: "system", action: "lead.viewed", metadata: {} });
  });

  test("rows cannot be changed or deleted (database trigger)", async () => {
    await recordAudit({ actorType: "system", action: "lead.viewed", entityId: "test-immutable" });
    const where = eq(auditLogs.entityId, "test-immutable");

    await expect(
      db.update(auditLogs).set({ action: "lead.updated" }).where(where)
    ).rejects.toMatchObject({
      cause: { message: "audit_logs is append-only" }
    });
    await expect(db.delete(auditLogs).where(where)).rejects.toMatchObject({
      cause: { message: "audit_logs rows must be kept for at least one year" }
    });
  });
});
