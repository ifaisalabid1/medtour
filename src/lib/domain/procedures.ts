export interface NumericRange {
  min: number;
  max: number;
}

/** Shown on procedure pages instead of prices. */
export interface ProcedureLogistics {
  durationHours?: NumericRange;
  hospitalStayDays?: NumericRange;
  stayInIndiaDays?: NumericRange; // after discharge, before travelling home
  returnToWorkDays?: NumericRange;
}

export const FAQ_PHASES = ["before", "during", "after"] as const;
export type FaqPhase = (typeof FAQ_PHASES)[number];

export interface ProcedureFaq {
  phase: FaqPhase;
  question: string;
  answer: string;
}

export const ROOM_CATEGORIES = ["general_ward", "twin_sharing", "single", "deluxe"] as const;
export type RoomCategory = (typeof ROOM_CATEGORIES)[number];
