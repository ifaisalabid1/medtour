import { pgEnum } from "drizzle-orm/pg-core";
import { ACCREDITATIONS, FACILITY_TYPES, MOU_STATUSES } from "#lib/domain/hospitals.js";
import { ROOM_CATEGORIES } from "#lib/domain/procedures.js";
import { ACTOR_TYPES } from "#lib/domain/audit.js";
import {
  DOCUMENT_KINDS,
  LEAD_INTENTS,
  LEAD_STATUSES,
  REPORTS_STATUSES,
  TRAVEL_TIMELINES
} from "#lib/domain/leads.js";

export const publishStatus = pgEnum("publish_status", ["draft", "published", "archived"]);
export const accreditation = pgEnum("accreditation", ACCREDITATIONS);
export const facilityType = pgEnum("facility_type", FACILITY_TYPES);
export const mouStatus = pgEnum("mou_status", MOU_STATUSES);
export const roomCategory = pgEnum("room_category", ROOM_CATEGORIES);
export const leadIntent = pgEnum("lead_intent", LEAD_INTENTS);
export const leadStatus = pgEnum("lead_status", LEAD_STATUSES);
export const travelTimeline = pgEnum("travel_timeline", TRAVEL_TIMELINES);
export const reportsStatus = pgEnum("reports_status", REPORTS_STATUSES);
export const documentKind = pgEnum("document_kind", DOCUMENT_KINDS);
export const actorType = pgEnum("actor_type", ACTOR_TYPES);
