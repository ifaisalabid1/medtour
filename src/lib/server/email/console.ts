import type { Logger } from "pino";
import type { EmailMessage, EmailTransport } from "./types.js";

/** Development only: prints the email instead of sending it. */
export function createConsoleTransport(logger: Logger): EmailTransport {
  return {
    async send(message: EmailMessage) {
      logger.info({ subject: message.subject }, `email to ${message.to}\n${message.text}`);
    }
  };
}
