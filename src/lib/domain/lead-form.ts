import {
  isSupportedCountry,
  parsePhoneNumberFromString,
  type CountryCode
} from "libphonenumber-js/min";
import * as z from "zod";
import { INDIAN_STATES } from "./india.js";
import { LEAD_INTENTS, REPORTS_STATUSES, TRAVEL_TIMELINES } from "./leads.js";

// Shared by the browser (instant feedback) and the server (the real check).

const country = z
  .string()
  .trim()
  .toUpperCase()
  .refine((code): code is CountryCode => isSupportedCountry(code), "Choose a country");

const slug = z
  .string()
  .regex(/^[a-z0-9]+(-[a-z0-9]+)*$/)
  .max(120);

const utmValue = z.string().trim().max(100);

export const leadFormSchema = z
  .object({
    fullName: z.string().trim().min(2, "Enter your full name").max(100),
    email: z.string().trim().toLowerCase().max(254).pipe(z.email("Enter a valid email address")),
    phone: z.string().trim().min(6, "Enter your phone or WhatsApp number").max(25),
    countryCode: country,
    indianState: z.enum(INDIAN_STATES).optional(),
    passportCountry: country.optional(),
    intent: z.enum(LEAD_INTENTS),
    description: z
      .string()
      .trim()
      .min(10, "Tell us a little more about the medical problem")
      .max(2000),
    reportsStatus: z.enum(REPORTS_STATUSES).optional(),
    travelTimeline: z.enum(TRAVEL_TIMELINES).optional(),
    needsVisaLetter: z.boolean().default(false),
    openToPaidTeleconsult: z.boolean().default(false),
    needsInsuranceHelp: z.boolean().default(false),
    consent: z.literal(true, "Please accept the consent notice to continue"),
    // Where the enquiry came from (page context and campaign)
    procedureSlug: slug.optional(),
    hospitalSlug: slug.optional(),
    doctorSlug: slug.optional(),
    sourcePath: z
      .string()
      .regex(/^\/(?!\/)/)
      .max(300)
      .optional(),
    utm: z
      .object({
        source: utmValue,
        medium: utmValue,
        campaign: utmValue,
        term: utmValue,
        content: utmValue
      })
      .partial()
      .optional()
  })
  .superRefine((form, ctx) => {
    if (form.countryCode === "IN" && !form.indianState) {
      ctx.addIssue({ code: "custom", path: ["indianState"], message: "Choose your state" });
    }
    if (!parsePhoneNumberFromString(form.phone, form.countryCode)?.isValid()) {
      ctx.addIssue({ code: "custom", path: ["phone"], message: "Enter a valid phone number" });
    }
  })
  .transform((form) => {
    const domestic = form.countryCode === "IN";
    const phone = parsePhoneNumberFromString(form.phone, form.countryCode);
    return {
      ...form,
      phone: phone?.number ?? form.phone, // E.164, e.g. +919876543210
      indianState: domestic ? form.indianState : undefined,
      passportCountry: domestic ? undefined : (form.passportCountry ?? form.countryCode),
      needsVisaLetter: domestic ? false : form.needsVisaLetter
    };
  });

export type LeadFormInput = z.input<typeof leadFormSchema>;
export type LeadForm = z.output<typeof leadFormSchema>;
