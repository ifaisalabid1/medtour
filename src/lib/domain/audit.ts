export const ACTOR_TYPES = ["staff", "patient", "system"] as const;
export type ActorType = (typeof ACTOR_TYPES)[number];
