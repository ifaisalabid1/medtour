import { describe, expect, test } from "vitest";
import { leadFormSchema, type LeadFormInput } from "./lead-form.js";

const domestic: LeadFormInput = {
  fullName: "Asha Kumari",
  email: " Asha@Example.COM ",
  phone: "98765 43210",
  countryCode: "in",
  indianState: "Bihar",
  intent: "treatment",
  description: "Knee pain for two years, advised replacement.",
  consent: true
};

const international: LeadFormInput = {
  fullName: "Chidi Okafor",
  email: "chidi@example.com",
  phone: "+234 801 234 5678",
  countryCode: "NG",
  intent: "medical_visa",
  description: "Needs CABG, cardiologist in Lagos referred.",
  needsVisaLetter: true,
  consent: true
};

/** Field paths that failed validation, e.g. ["phone"]. */
function failedFields(input: unknown) {
  const result = leadFormSchema.safeParse(input);
  return result.success ? [] : result.error.issues.map((issue) => issue.path.join("."));
}

describe("leadFormSchema", () => {
  test("normalises a domestic lead", () => {
    expect(leadFormSchema.parse(domestic)).toMatchObject({
      email: "asha@example.com",
      phone: "+919876543210",
      countryCode: "IN",
      indianState: "Bihar",
      passportCountry: undefined,
      needsVisaLetter: false
    });
  });

  test("normalises an international lead; passport country defaults to residence", () => {
    expect(leadFormSchema.parse(international)).toMatchObject({
      phone: "+2348012345678",
      passportCountry: "NG",
      indianState: undefined,
      needsVisaLetter: true
    });
  });

  test("requires a state for Indian residents", () => {
    expect(failedFields({ ...domestic, indianState: undefined })).toEqual(["indianState"]);
  });

  test("never keeps a visa letter request for domestic patients", () => {
    expect(leadFormSchema.parse({ ...domestic, needsVisaLetter: true }).needsVisaLetter).toBe(
      false
    );
  });

  test("rejects invalid phone numbers, emails and countries", () => {
    expect(failedFields({ ...domestic, phone: "12345" })).toContain("phone");
    expect(failedFields({ ...domestic, email: "not-an-email" })).toContain("email");
    expect(failedFields({ ...domestic, countryCode: "XX" })).toContain("countryCode");
  });

  test("requires consent", () => {
    expect(failedFields({ ...domestic, consent: false })).toEqual(["consent"]);
  });

  test("rejects external or protocol-relative source paths", () => {
    expect(failedFields({ ...domestic, sourcePath: "https://evil.com" })).toEqual(["sourcePath"]);
    expect(failedFields({ ...domestic, sourcePath: "//evil.com" })).toEqual(["sourcePath"]);
    expect(failedFields({ ...domestic, sourcePath: "/hospital/apollo-chennai" })).toEqual([]);
  });
});
