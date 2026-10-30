import type { EmailMessage } from "../types.js";
import { escapeHtml } from "./escape.js";

/** To the patient. Confirms receipt only: no medical details ever go into email. */
export function leadReceivedEmail(input: {
  ref: string;
  fullName: string;
}): Pick<EmailMessage, "subject" | "html" | "text"> {
  const name = input.fullName.split(" ")[0] ?? input.fullName;
  return {
    subject: `We received your request (${input.ref})`,
    text: `Dear ${name},

Thank you for contacting Medtour. Your request reference is ${input.ref}.

A case manager will review your request and contact you on WhatsApp or email within 24 to 48 hours. Please quote ${input.ref} in any message to us.

Medtour`,
    html: `<!doctype html>
<html>
  <body style="font-family: Arial, sans-serif; color: #111; line-height: 1.5">
    <p>Dear ${escapeHtml(name)},</p>
    <p>Thank you for contacting Medtour. Your request reference is <strong>${input.ref}</strong>.</p>
    <p>A case manager will review your request and contact you on WhatsApp or email within 24 to 48 hours. Please quote ${input.ref} in any message to us.</p>
    <p>Medtour</p>
  </body>
</html>`
  };
}
