import type { EmailMessage } from "../types.js";

/** To the team. Deliberately contains no patient data: staff open the lead in the admin. */
export function newLeadAlertEmail(input: {
  ref: string;
  intent: string;
  funnel: "domestic" | "international";
  adminUrl: string;
}): Pick<EmailMessage, "subject" | "html" | "text"> {
  const summary = `${input.funnel === "domestic" ? "Domestic" : "International"} · ${input.intent.replaceAll("_", " ")}`;
  return {
    subject: `New enquiry ${input.ref} (${summary})`,
    text: `New enquiry ${input.ref}: ${summary}\n\nOpen it in the admin: ${input.adminUrl}`,
    html: `<!doctype html>
<html>
  <body style="font-family: Arial, sans-serif; color: #111; line-height: 1.5">
    <p>New enquiry <strong>${input.ref}</strong>: ${summary}</p>
    <p><a href="${input.adminUrl}">Open it in the admin</a></p>
  </body>
</html>`
  };
}
