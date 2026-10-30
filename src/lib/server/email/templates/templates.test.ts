import { expect, test } from "vitest";
import { escapeHtml } from "./escape.js";
import { leadReceivedEmail } from "./lead-received.js";

test("escapeHtml neutralises markup", () => {
  expect(escapeHtml(`<script>alert("x")</script> & 'y'`)).toBe(
    "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt; &amp; &#39;y&#39;"
  );
});

test("patient email escapes the visitor's name in HTML", () => {
  const email = leadReceivedEmail({ ref: "MT-1001", fullName: "<img src=x onerror=alert(1)> Doe" });
  expect(email.html).not.toContain("<img");
  expect(email.html).toContain("&lt;img");
});
