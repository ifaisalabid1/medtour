const ADMIN_HOME = "/admin";

/**
 * Where to send staff after sign-in. `redirectTo` comes from the URL, so anyone can craft it:
 * only admin pages on this site are allowed, never another origin or the login page itself.
 */
export function safeAdminRedirect(redirectTo: string | null | undefined): string {
  if (!redirectTo) return ADMIN_HOME;

  let url: URL;
  try {
    url = new URL(redirectTo, "http://localhost"); // a relative path keeps this placeholder origin
  } catch {
    return ADMIN_HOME;
  }

  const sameOrigin = url.origin === "http://localhost" && redirectTo.startsWith("/");
  const isAdmin = url.pathname === ADMIN_HOME || url.pathname.startsWith(`${ADMIN_HOME}/`);
  const isLogin = url.pathname === `${ADMIN_HOME}/login`;

  return sameOrigin && isAdmin && !isLogin ? url.pathname + url.search : ADMIN_HOME;
}
