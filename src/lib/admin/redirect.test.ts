import { describe, expect, test } from "vitest";
import { safeAdminRedirect } from "./redirect.js";

describe("safeAdminRedirect", () => {
  test("keeps admin paths and their query string", () => {
    expect(safeAdminRedirect("/admin/leads?status=new")).toBe("/admin/leads?status=new");
    expect(safeAdminRedirect("/admin")).toBe("/admin");
  });

  test("falls back to the dashboard when missing", () => {
    expect(safeAdminRedirect(null)).toBe("/admin");
    expect(safeAdminRedirect("")).toBe("/admin");
  });

  test("rejects other origins, including protocol-relative and backslash tricks", () => {
    expect(safeAdminRedirect("https://evil.example/admin")).toBe("/admin");
    expect(safeAdminRedirect("//evil.example/admin")).toBe("/admin");
    expect(safeAdminRedirect("/\\evil.example/admin")).toBe("/admin");
    expect(safeAdminRedirect("javascript:alert(1)")).toBe("/admin");
  });

  test("rejects public pages, look-alike prefixes and the login page", () => {
    expect(safeAdminRedirect("/hospitals")).toBe("/admin");
    expect(safeAdminRedirect("/administrator")).toBe("/admin");
    expect(safeAdminRedirect("/admin/login")).toBe("/admin");
    expect(safeAdminRedirect("/admin/../hospitals")).toBe("/admin");
  });
});
