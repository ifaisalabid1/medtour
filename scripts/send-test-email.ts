// Usage: bun scripts/send-test-email.ts you@example.com
import { createSesTransport } from "#lib/server/email/ses.js";

const to = process.argv[2];
const { SES_REGION, SES_ACCESS_KEY_ID, SES_SECRET_ACCESS_KEY, EMAIL_FROM } = process.env;

if (!to || !SES_REGION || !SES_ACCESS_KEY_ID || !SES_SECRET_ACCESS_KEY || !EMAIL_FROM) {
  console.error("Usage: bun scripts/send-test-email.ts <to>  (needs SES_* and EMAIL_FROM in .env)");
  process.exit(1);
}

const ses = createSesTransport({
  region: SES_REGION,
  accessKeyId: SES_ACCESS_KEY_ID,
  secretAccessKey: SES_SECRET_ACCESS_KEY,
  from: EMAIL_FROM
});

await ses.send({
  to,
  subject: "SES test",
  html: "<p>Amazon SES is working.</p>",
  text: "Amazon SES is working."
});
console.log(`Sent to ${to}`);
