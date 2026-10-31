import { redirect } from "@sveltejs/kit";
import { SIDEBAR_COOKIE_NAME } from "#lib/components/ui/sidebar/constants.js";
import type { LayoutServerLoad } from "./$types";

export const load: LayoutServerLoad = ({ locals, cookies }) => {
  // hooks.server.ts already redirects anonymous visitors; this also narrows the type for pages
  if (!locals.user) redirect(303, "/admin/login");

  return {
    user: {
      id: locals.user.id,
      name: locals.user.name,
      email: locals.user.email,
      isAdmin: locals.user.role === "admin"
    },
    sidebarOpen: cookies.get(SIDEBAR_COOKIE_NAME) !== "false"
  };
};
