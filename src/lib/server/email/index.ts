import { dev } from "$app/env";
import {
  EMAIL_FROM,
  EMAIL_TRANSPORT,
  SES_ACCESS_KEY_ID,
  SES_REGION,
  SES_SECRET_ACCESS_KEY
} from "$app/env/private";
import { logger } from "../logger.js";
import { createConsoleTransport } from "./console.js";
import { createSesTransport } from "./ses.js";
import type { EmailMessage, EmailTransport } from "./types.js";

export type { EmailMessage } from "./types.js";

function createTransport(): EmailTransport {
  if (EMAIL_TRANSPORT === "console") {
    if (!dev) throw new Error("EMAIL_TRANSPORT=console is not allowed in production");
    return createConsoleTransport(logger);
  }
  if (!SES_REGION || !SES_ACCESS_KEY_ID || !SES_SECRET_ACCESS_KEY) {
    throw new Error(
      "EMAIL_TRANSPORT=ses requires SES_REGION, SES_ACCESS_KEY_ID and SES_SECRET_ACCESS_KEY"
    );
  }
  return createSesTransport({
    region: SES_REGION,
    accessKeyId: SES_ACCESS_KEY_ID,
    secretAccessKey: SES_SECRET_ACCESS_KEY,
    from: EMAIL_FROM
  });
}

// Created on first use: `vite build` imports this module, and build machines have no SES secrets
let transport: EmailTransport | undefined;

export async function sendEmail(message: EmailMessage): Promise<void> {
  transport ??= createTransport();
  await transport.send(message);
  logger.info({ subject: message.subject }, "email sent");
}
