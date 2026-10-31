import { getDashboardStats } from "#lib/server/queries/admin/dashboard.js";
import type { PageServerLoad } from "./$types";

export const load: PageServerLoad = async () => ({
  stats: await getDashboardStats()
});
