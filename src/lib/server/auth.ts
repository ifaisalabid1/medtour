import { betterAuth } from "better-auth";
import { drizzleAdapter } from "better-auth/adapters/drizzle";
import { createAuthMiddleware } from "better-auth/api";
import { admin, emailOTP } from "better-auth/plugins";
import { sveltekitCookies } from "better-auth/svelte-kit";
import { getRequestEvent } from "$app/server";
import { BETTER_AUTH_SECRET, BETTER_AUTH_URL } from "$app/env/private";
import { recordAudit, requestMeta } from "./audit.js";
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
        ...requestMeta(getRequestEvent())
      });
    })
  },
  databaseHooks: {
    session: {
      delete: {
        after: async (session, ctx) => {
          await recordAudit({
            actorType: "staff",
            actorId: session.userId,
            action: ctx?.path === "/sign-out" ? "auth.sign_out" : "auth.session_revoked",
            entityType: "user",
            entityId: session.userId,
            ...requestMeta(getRequestEvent())
          });
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
