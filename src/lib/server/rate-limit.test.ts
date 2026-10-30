import { RateLimiterMemory } from "rate-limiter-flexible";
import { expect, test } from "vitest";
import { consumeOrRetryAfter } from "./rate-limit.js";

test("allows up to the limit, then returns seconds to wait", async () => {
  const limiter = new RateLimiterMemory({ points: 2, duration: 60 });
  expect(await consumeOrRetryAfter(limiter, "203.0.113.9")).toBeNull();
  expect(await consumeOrRetryAfter(limiter, "203.0.113.9")).toBeNull();

  const retryAfter = await consumeOrRetryAfter(limiter, "203.0.113.9");
  expect(retryAfter).toBeGreaterThan(0);
  expect(retryAfter).toBeLessThanOrEqual(60);

  // Other visitors are unaffected
  expect(await consumeOrRetryAfter(limiter, "198.51.100.1")).toBeNull();
});
