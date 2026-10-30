CREATE TYPE "public"."publish_status" AS ENUM('draft', 'published', 'archived');--> statement-breakpoint
CREATE TABLE "cities" (
	"id" uuid PRIMARY KEY DEFAULT uuidv7() NOT NULL,
	"slug" text NOT NULL,
	"name" text NOT NULL,
	"state" text NOT NULL,
	"airport_code" char(3),
	"airport_name" text,
	"summary" text,
	"sort_order" smallint DEFAULT 0 NOT NULL,
	"meta_title" text,
	"meta_description" text,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "cities_slug_unique" UNIQUE("slug"),
	CONSTRAINT "cities_slug_format" CHECK ("cities"."slug" ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
	CONSTRAINT "cities_airport_code_format" CHECK ("cities"."airport_code" ~ '^[A-Z]{3}$')
);
--> statement-breakpoint
CREATE TABLE "medical_reviewers" (
	"id" uuid PRIMARY KEY DEFAULT uuidv7() NOT NULL,
	"slug" text NOT NULL,
	"full_name" text NOT NULL,
	"specialty_id" uuid NOT NULL,
	"qualifications" text[] DEFAULT '{}' NOT NULL,
	"affiliation" text,
	"practice_since" smallint,
	"registration_number" text NOT NULL,
	"medical_council" text NOT NULL,
	"bio" text,
	"profile_urls" text[] DEFAULT '{}' NOT NULL,
	"status" "publish_status" DEFAULT 'draft' NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "medical_reviewers_slug_unique" UNIQUE("slug"),
	CONSTRAINT "medical_reviewers_slug_format" CHECK ("medical_reviewers"."slug" ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
	CONSTRAINT "medical_reviewers_practice_since_range" CHECK ("medical_reviewers"."practice_since" >= 1950)
);
--> statement-breakpoint
CREATE TABLE "specialties" (
	"id" uuid PRIMARY KEY DEFAULT uuidv7() NOT NULL,
	"slug" text NOT NULL,
	"name" text NOT NULL,
	"parent_id" uuid,
	"summary" text,
	"icon" text,
	"sort_order" smallint DEFAULT 0 NOT NULL,
	"meta_title" text,
	"meta_description" text,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "specialties_slug_unique" UNIQUE("slug"),
	CONSTRAINT "specialties_slug_format" CHECK ("specialties"."slug" ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
	CONSTRAINT "specialties_not_own_parent" CHECK ("specialties"."parent_id" <> "specialties"."id")
);
--> statement-breakpoint
ALTER TABLE "medical_reviewers" ADD CONSTRAINT "medical_reviewers_specialty_id_specialties_id_fk" FOREIGN KEY ("specialty_id") REFERENCES "public"."specialties"("id") ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "specialties" ADD CONSTRAINT "specialties_parent_id_specialties_id_fk" FOREIGN KEY ("parent_id") REFERENCES "public"."specialties"("id") ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
CREATE INDEX "medical_reviewers_specialty_id_index" ON "medical_reviewers" USING btree ("specialty_id");--> statement-breakpoint
CREATE INDEX "specialties_parent_id_index" ON "specialties" USING btree ("parent_id");