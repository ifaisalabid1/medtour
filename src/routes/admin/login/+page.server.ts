import { redirect } from "@sveltejs/kit";
import { safeAdminRedirect } from "#lib/admin/redirect.js";
import type { PageServerLoad } from "./$types";

export const load: PageServerLoad = ({ locals, url }) => {
  // Already signed in: skip the form
  if (locals.user) redirect(303, safeAdminRedirect(url.searchParams.get("redirectTo")));
};
