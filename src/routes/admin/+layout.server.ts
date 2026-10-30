import type { LayoutServerLoad } from "./$types";

export const load: LayoutServerLoad = ({ locals }) => {
  // hooks.server.ts has already redirected anonymous visitors (except on /admin/login)
  return {
    user: locals.user && {
      name: locals.user.name,
      email: locals.user.email,
      role: locals.user.role
    }
  };
};
