/**
 * Every public URL of the site, in one place. Pages, links, the sitemap and emails all build
 * URLs here, so they can never disagree. One URL segment per slug; India is implied.
 */
export const paths = {
  home: () => "/",
  specialty: (specialty: string) => `/specialties/${specialty}`,

  hospitals: () => "/hospitals",
  hospitalsInCity: (city: string) => `/hospitals/${city}`,
  hospitalsBySpecialtyInCity: (specialty: string, city: string) =>
    `/hospitals/${specialty}/${city}`,
  hospital: (slug: string) => `/hospital/${slug}`,

  doctors: () => "/doctors",
  doctorsBySpecialty: (specialty: string) => `/doctors/${specialty}`,
  doctorsBySpecialtyInCity: (specialty: string, city: string) => `/doctors/${specialty}/${city}`,
  doctor: (slug: string) => `/doctor/${slug}`,

  treatments: () => "/treatments",
  treatment: (slug: string) => `/treatments/${slug}`,

  medicalVisa: () => "/medical-visa-india",
  reviewerBoard: () => "/medical-reviewer-board",
  editorialPolicy: () => "/editorial-policy",
  about: () => "/about",
  contact: () => "/contact",
  privacy: () => "/privacy"
} as const;
