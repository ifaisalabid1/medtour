import { SESv2Client, SendEmailCommand } from "@aws-sdk/client-sesv2";
import type { EmailMessage, EmailTransport } from "./types.js";

export interface SesConfig {
  region: string;
  accessKeyId: string;
  secretAccessKey: string;
  from: string;
}

export function createSesTransport(config: SesConfig): EmailTransport {
  const client = new SESv2Client({
    region: config.region,
    credentials: { accessKeyId: config.accessKeyId, secretAccessKey: config.secretAccessKey }
  });

  return {
    async send(message: EmailMessage) {
      await client.send(
        new SendEmailCommand({
          FromEmailAddress: config.from,
          Destination: { ToAddresses: [message.to] },
          ReplyToAddresses: message.replyTo ? [message.replyTo] : undefined,
          Content: {
            Simple: {
              Subject: { Data: message.subject, Charset: "UTF-8" },
              Body: {
                Html: { Data: message.html, Charset: "UTF-8" },
                Text: { Data: message.text, Charset: "UTF-8" }
              }
            }
          }
        })
      );
    }
  };
}
