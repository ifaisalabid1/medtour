import { readdirSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { expect, test } from "vitest";

// Static guard for the "no public prices" rule: public query files must never reference
// admin-only tables or use query shapes that return every column.
const FORBIDDEN: [RegExp, string][] = [
  [/\b(hospitalInternal|doctorInternal|hospitalProcedureTariffs)\b/, "imports an admin-only table"],
  [
    /\b(hospital_internal|doctor_internal|hospital_procedure_tariffs)\b/,
    "references an admin-only table in SQL"
  ],
  [/\.select\(\s*\)/, "uses select() without listing columns"],
  [/\bgetTableColumns\b/, "spreads every column of a table"],
  [/\bdb\.query\./, "uses the relational API, which returns every column by default"]
];

const dir = fileURLToPath(new URL(".", import.meta.url));
const files = readdirSync(dir).filter((f) => f.endsWith(".ts") && !f.endsWith(".test.ts"));

test("there are public query files to check", () => {
  expect(files.length).toBeGreaterThan(0);
});

test.each(files)("%s only touches public data", (file) => {
  const source = readFileSync(dir + file, "utf8");
  const violations = FORBIDDEN.filter(([pattern]) => pattern.test(source)).map(([, why]) => why);
  expect(violations).toEqual([]);
});
