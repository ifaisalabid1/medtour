import { defineEnvVars } from "@sveltejs/kit/env";
import * as z from "zod";

// Treats `KEY=` (empty) in .env the same as an unset variable
const optionalSecret = (value: string | undefined) => value || undefined;

export const variables = defineEnvVars({
  DATABASE_URL: {
    description: "PostgreSQL connection string.",
    schema: z.url({ protocol: /^postgres(ql)?$/ })
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
  SES_SECRET_ACCESS_KEY: { description: "Secret for SES_ACCESS_KEY_ID.", schema: optionalSecret }
});
