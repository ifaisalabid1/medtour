export const ACCREDITATIONS = ["nabh", "jci", "nabl"] as const;
export type Accreditation = (typeof ACCREDITATIONS)[number];

export const FACILITY_TYPES = ["multi_specialty", "super_specialty", "single_specialty"] as const;
export type FacilityType = (typeof FACILITY_TYPES)[number];

/** Six-pillar patient services matrix shown on hospital profiles. */
export const AMENITY_PILLARS = [
  "comfort",
  "food",
  "money",
  "support",
  "transport",
  "language"
] as const;
export type AmenityPillar = (typeof AMENITY_PILLARS)[number];
export type HospitalAmenities = Partial<Record<AmenityPillar, string[]>>;

export const MOU_STATUSES = ["none", "negotiating", "signed", "expired"] as const;
export type MouStatus = (typeof MOU_STATUSES)[number];
