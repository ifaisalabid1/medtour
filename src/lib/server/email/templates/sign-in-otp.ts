import type { EmailMessage } from "../types.js";

export function signInOtpEmail(otp: string): Pick<EmailMessage, "subject" | "html" | "text"> {
  return {
    subject: `${otp} is your Medtour sign-in code`,
    text: `Your Medtour sign-in code is ${otp}. It expires in 5 minutes.\n\nIf you did not try to sign in, you can ignore this email.`,
    html: `<!doctype html>
<html>
  <body style="font-family: Arial, sans-serif; color: #111; line-height: 1.5">
    <p>Your Medtour sign-in code is:</p>
    <p style="font-size: 28px; font-weight: bold; letter-spacing: 6px">${otp}</p>
    <p>It expires in 5 minutes.</p>
    <p style="color: #666; font-size: 13px">If you did not try to sign in, you can ignore this email.</p>
  </body>
</html>`
  };
}
