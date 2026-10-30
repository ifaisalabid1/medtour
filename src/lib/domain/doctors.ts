export const WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"] as const;
export type Weekday = (typeof WEEKDAYS)[number];

/** One OPD session. Times are 24h "HH:MM" in IST. No fees, by design. */
export interface OpdSlot {
  day: Weekday;
  opens: string;
  closes: string;
}

export interface EducationEntry {
  degree: string;
  institution: string;
  year?: number;
}

/** The NMC guidelines require the awarding body and year for any award shown. */
export interface AwardEntry {
  title: string;
  awardedBy: string;
  year: number;
}

export interface WorkEntry {
  role: string;
  organization: string;
  fromYear?: number;
  toYear?: number;
}
