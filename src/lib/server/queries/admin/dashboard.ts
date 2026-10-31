import { count, gte } from "drizzle-orm";
import { LEAD_STATUSES, type LeadStatus } from "#lib/domain/leads.js";
import { db } from "../../db/index.js";
import { doctors, hospitals, patientLeads, procedures } from "../../db/schema/index.js";

// ADMIN ONLY. Never import from public pages or src/lib/server/queries/public.

const DAY_MS = 24 * 60 * 60 * 1000;

/** Rows per publish status, e.g. { draft: 3, published: 12, archived: 0 }. */
async function publishCounts(table: typeof hospitals | typeof doctors | typeof procedures) {
  const rows = await db
    .select({ status: table.status, total: count() })
    .from(table)
    .groupBy(table.status);
  const counts = { draft: 0, published: 0, archived: 0 };
  for (const row of rows) counts[row.status] = row.total;
  return counts;
}

/** Headline numbers for the admin dashboard. */
export async function getDashboardStats(now = new Date()) {
  const [byStatus, [recent], hospitalCounts, doctorCounts, procedureCounts] = await Promise.all([
    db
      .select({ status: patientLeads.status, total: count() })
      .from(patientLeads)
      .groupBy(patientLeads.status),
    db
      .select({ total: count() })
      .from(patientLeads)
      .where(gte(patientLeads.createdAt, new Date(now.getTime() - 7 * DAY_MS))),
    publishCounts(hospitals),
    publishCounts(doctors),
    publishCounts(procedures)
  ]);

  const leadsByStatus = Object.fromEntries(LEAD_STATUSES.map((status) => [status, 0])) as Record<
    LeadStatus,
    number
  >;
  for (const row of byStatus) leadsByStatus[row.status] = row.total;

  return {
    leadsByStatus,
    leadsLast7Days: recent?.total ?? 0,
    hospitals: hospitalCounts,
    doctors: doctorCounts,
    procedures: procedureCounts
  };
}

export type DashboardStats = Awaited<ReturnType<typeof getDashboardStats>>;
