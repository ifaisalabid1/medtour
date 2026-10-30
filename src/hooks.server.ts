import { redirect } from "@sveltejs/kit";
import { sequence, type Handle, type HandleServerError } from "@sveltejs/kit/hooks";
import { svelteKitHandler } from "better-auth/svelte-kit";
import { building } from "$app/env";
import { auth } from "#lib/server/auth.js";
import { logger } from "#lib/server/logger.js";

const isAdminPath = (pathname: string) => pathname === "/admin" || pathname.startsWith("/admin/");

/**
 * Loads the staff session, but only on /admin. Public pages never touch the session,
 * so they stay cacheable and never receive a Set-Cookie header.
 */
const authentication: Handle = async ({ event, resolve }) => {
  event.locals.user = null;
  event.locals.session = null;

  if (!building && isAdminPath(event.url.pathname)) {
    const result = await auth.api.getSession({ headers: event.request.headers });
    event.locals.user = result?.user ?? null;
    event.locals.session = result?.session ?? null;
  }

  // Serves better-auth's own endpoints under /api/auth/*
  return svelteKitHandler({ event, resolve, auth, building });
};

const adminGuard: Handle = async ({ event, resolve }) => {
  const { pathname, search } = event.url;
  if (isAdminPath(pathname) && pathname !== "/admin/login" && !event.locals.user) {
    redirect(303, `/admin/login?redirectTo=${encodeURIComponent(pathname + search)}`);
  }
  return resolve(event);
};

export const handle = sequence(authentication, adminGuard);

export const handleError: HandleServerError = ({ kind, error, event }) => {
  if (kind === "unknown") {
    const errorId = crypto.randomUUID();
    logger.error({ err: error, errorId, path: event.url.pathname }, "unhandled server error");
    return { message: `Something went wrong (ref ${errorId.slice(0, 8)})` };
  }
};
