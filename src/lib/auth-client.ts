import { createAuthClient } from "better-auth/client";
import { emailOTPClient } from "better-auth/client/plugins";

/** Browser client for better-auth's /api/auth endpoints. Used by the admin panel only. */
export const authClient = createAuthClient({
  plugins: [emailOTPClient()]
});
