import { defineEnvVars } from "@sveltejs/kit/env";
import * as z from "zod";

// Treats `KEY=` (empty) in .env the same as an unset variable
const optionalSecret = (value: string | undefined) => value || undefined;

export const variables = defineEnvVars({
  DATABASE_URL: {
    description: "PostgreSQL connection string.",
    schema: z.url({ protocol: /^postgres(ql)?$/ })
  },
  BETTER_AUTH_SECRET: {
    description: "Signs session cookies. Generate with: openssl rand -base64 32",
    schema: z.string().min(32)
  },
  SITE_URL: {
    description:
      "Public origin of the site, e.g. https://medtour.example (http://localhost:5173 in dev).",
    schema: z.url()
  },
  LOG_LEVEL: {
    description: "pino log level.",
    schema: z.enum(["fatal", "error", "warn", "info", "debug", "trace"]).default("info")
  },
  EMAIL_TRANSPORT: {
    description: "`ses` sends real email; `console` logs it (development only).",
    schema: z.enum(["ses", "console"]).default("console")
  },
  EMAIL_FROM: {
    description: 'Sender, e.g. "Medtour <care@example.com>". Must be an SES-verified identity.',
    schema: z.string().min(3)
  },
  SES_REGION: {
    description: "AWS region of the SES identity, e.g. ap-south-1.",
    schema: optionalSecret
  },
  SES_ACCESS_KEY_ID: { description: "IAM key limited to ses:SendEmail.", schema: optionalSecret },
  SES_SECRET_ACCESS_KEY: { description: "Secret for SES_ACCESS_KEY_ID.", schema: optionalSecret },
  LEADS_NOTIFY_EMAIL: {
    description: "Team inbox notified of every new enquiry.",
    schema: z.email()
  },
  R2_ENDPOINT: {
    description: "Cloudflare R2 S3 endpoint: https://<account-id>.r2.cloudflarestorage.com",
    schema: z.url()
  },
  R2_ACCESS_KEY_ID: { description: "R2 API token access key ID.", schema: z.string().min(1) },
  R2_SECRET_ACCESS_KEY: { description: "R2 API token secret.", schema: z.string().min(1) },
  R2_PRIVATE_BUCKET: {
    description: "Private bucket for patient documents (no public access).",
    schema: z.string().min(1)
  },
  UPLOAD_GRANT_SECRET: {
    description: "Signs patient upload grants. Generate with: openssl rand -base64 32",
    schema: z.string().min(32)
  },
  TURNSTILE_SECRET_KEY: {
    description:
      "Cloudflare Turnstile secret. Dev: 1x0000000000000000000000000000000AA (always passes).",
    schema: z.string().min(1)
  },
  PUBLIC_TURNSTILE_SITE_KEY: {
    description: "Cloudflare Turnstile site key for the widget. Dev: 1x00000000000000000000AA.",
    public: true,
    schema: z.string().min(1)
  }
});
