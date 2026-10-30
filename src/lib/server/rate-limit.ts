import { RateLimiterMemory, RateLimiterRes } from "rate-limiter-flexible";

// In-memory counters: correct for one server process (our VPS). Use a shared store
// (Postgres or Redis) if the app ever runs as several processes.

/** Enquiries per IP: 5 per hour. */
export const leadSubmissionLimiter = new RateLimiterMemory({
  keyPrefix: "lead",
  points: 5,
  duration: 60 * 60
});

/** Spends one point. Returns null if allowed, or the seconds to wait if the limit is reached. */
export async function consumeOrRetryAfter(
  limiter: RateLimiterMemory,
  key: string
): Promise<number | null> {
  try {
    await limiter.consume(key);
    return null;
  } catch (rejection) {
    if (rejection instanceof RateLimiterRes) return Math.ceil(rejection.msBeforeNext / 1000);
    throw rejection;
  }
}
