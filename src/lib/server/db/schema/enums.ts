import { pgEnum } from "drizzle-orm/pg-core";
import { ACCREDITATIONS, FACILITY_TYPES, MOU_STATUSES } from "#lib/domain/hospitals.js";
import { ROOM_CATEGORIES } from "#lib/domain/procedures.js";

export const publishStatus = pgEnum("publish_status", ["draft", "published", "archived"]);
export const accreditation = pgEnum("accreditation", ACCREDITATIONS);
export const facilityType = pgEnum("facility_type", FACILITY_TYPES);
export const mouStatus = pgEnum("mou_status", MOU_STATUSES);
export const roomCategory = pgEnum("room_category", ROOM_CATEGORIES);
