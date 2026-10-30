import pino from "pino";
import { dev } from "$app/env";
import { LOG_LEVEL } from "$app/env/private";

export const logger = pino({
  level: LOG_LEVEL,
  // Never let personal or secret data reach the logs
  redact: {
    paths: ["*.email", "*.phone", "*.otp", "*.password", "*.authorization", "*.cookie"],
    censor: "[redacted]"
  },
  ...(dev && { transport: { target: "pino-pretty", options: { colorize: true } } })
});
