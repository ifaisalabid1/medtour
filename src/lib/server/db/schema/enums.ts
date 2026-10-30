import { pgEnum } from "drizzle-orm/pg-core";

export const publishStatus = pgEnum("publish_status", ["draft", "published", "archived"]);
