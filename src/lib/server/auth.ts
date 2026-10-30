import { betterAuth } from "better-auth";
import { drizzleAdapter } from "better-auth/adapters/drizzle";
import { createAuthMiddleware } from "better-auth/api";
import { admin, emailOTP } from "better-auth/plugins";
import { sveltekitCookies } from "better-auth/svelte-kit";
import { getRequestEvent } from "$app/server";
import { BETTER_AUTH_SECRET, BETTER_AUTH_URL } from "$app/env/private";
import { currentRequestMeta, recordAudit } from "./audit.js";
import { db } from "./db/index.js";
import { accounts, rateLimits, sessions, users, verifications } from "./db/schema/index.js";
import { sendEmail } from "./email/index.js";
import { signInOtpEmail } from "./email/templates/sign-in-otp.js";
import { logger } from "./logger.js";

const MINUTE = 60;
const HOUR = 60 * MINUTE;

export const auth = betterAuth({
  appName: "Medtour",
  baseURL: BETTER_AUTH_URL,
  secret: BETTER_AUTH_SECRET,
  database: drizzleAdapter(db, {
    provider: "pg",
    schema: {
      user: users,
      session: sessions,
      account: accounts,
      verification: verifications,
      rateLimit: rateLimits
    }
  }),
  advanced: {
    database: { generateId: false } // Postgres generates UUIDv7 ids
  },
  // Staff can see medical data: short sessions, refreshed while active
  session: {
    expiresIn: 12 * HOUR,
    updateAge: 1 * HOUR
  },
  hooks: {
    after: createAuthMiddleware(async (ctx) => {
      if (ctx.path !== "/sign-in/email-otp") return;
      const signedIn = ctx.context.newSession;
      await recordAudit({
        actorType: "staff",
        actorId: signedIn?.user.id ?? null,
        action: signedIn ? "auth.sign_in" : "auth.sign_in_failed",
        entityType: "user",
        entityId: signedIn?.user.id,
        // For failures, keep the attempted address so repeated attacks can be traced
        metadata: signedIn
          ? {}
          : {
              attemptedEmail: String(ctx.body?.email ?? "")
                .toLowerCase()
                .slice(0, 254)
            },
        ...currentRequestMeta()
      });
    })
  },
  databaseHooks: {
    session: {
      delete: {
        after: async (session, ctx) => {
          const base = {
            entityType: "user",
            entityId: session.userId,
            metadata: { via: ctx?.path ?? "internal" },
            ...currentRequestMeta()
          };

          if (ctx?.path === "/sign-out") {
            await recordAudit({
              ...base,
              actorType: "staff",
              actorId: session.userId,
              action: "auth.sign_out"
            });
          } else if (session.expiresAt <= new Date()) {
            await recordAudit({ ...base, actorType: "system", action: "auth.session_expired" });
          } else {
            // Revoked by someone else, e.g. an admin: record who made the request,
            // not the session's owner (who is the subject, in entityId)
            const actorId = ctx?.context.session?.user.id ?? null;
            await recordAudit({
              ...base,
              actorType: actorId ? "staff" : "system",
              actorId,
              action: "auth.session_revoked"
            });
          }
        }
      }
    }
  },
  rateLimit: {
    enabled: true,
    storage: "database",
    customRules: {
      "/email-otp/send-verification-otp": { window: 10 * MINUTE, max: 3 },
      "/sign-in/email-otp": { window: 10 * MINUTE, max: 5 }
    }
  },
  plugins: [
    emailOTP({
      disableSignUp: true, // only staff created by an admin can sign in
      otpLength: 6,
      expiresIn: 5 * MINUTE,
      allowedAttempts: 3,
      async sendVerificationOTP({ email, otp, type }) {
        if (type !== "sign-in") return;
        // Not awaited (as better-auth recommends): a slow SES call must not make
        // known emails respond slower than unknown ones
        void sendEmail({ to: email, ...signInOtpEmail(otp) }).catch((err) =>
          logger.error({ err }, "failed to send sign-in OTP")
        );
      }
    }),
    admin(),
    sveltekitCookies(getRequestEvent) // must be last
  ]
});

export type AuthSession = typeof auth.$Infer.Session;
