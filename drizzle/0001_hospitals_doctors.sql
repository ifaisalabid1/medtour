CREATE TYPE "public"."accreditation" AS ENUM('nabh', 'jci', 'nabl');--> statement-breakpoint
CREATE TYPE "public"."facility_type" AS ENUM('multi_specialty', 'super_specialty', 'single_specialty');--> statement-breakpoint
CREATE TYPE "public"."mou_status" AS ENUM('none', 'negotiating', 'signed', 'expired');--> statement-breakpoint
CREATE TABLE "doctor_hospitals" (
	"doctor_id" uuid NOT NULL,
	"hospital_id" uuid NOT NULL,
	"role" text,
	"is_primary" boolean DEFAULT false NOT NULL,
	"opd_schedule" jsonb DEFAULT '[]'::jsonb NOT NULL,
	CONSTRAINT "doctor_hospitals_doctor_id_hospital_id_pk" PRIMARY KEY("doctor_id","hospital_id")
);
--> statement-breakpoint
CREATE TABLE "doctor_internal" (
	"doctor_id" uuid PRIMARY KEY NOT NULL,
	"opd_fee_inr" integer,
	"teleconsult_fee_inr" integer,
	"secretary_phone" text,
	"escalation_email" text,
	"notes" text,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "doctor_internal_fees_non_negative" CHECK ("doctor_internal"."opd_fee_inr" >= 0 and "doctor_internal"."teleconsult_fee_inr" >= 0)
);
--> statement-breakpoint
CREATE TABLE "doctors" (
	"id" uuid PRIMARY KEY DEFAULT uuidv7() NOT NULL,
	"slug" text NOT NULL,
	"full_name" text NOT NULL,
	"designation" text,
	"primary_specialty_id" uuid NOT NULL,
	"qualifications" text[] DEFAULT '{}' NOT NULL,
	"practice_since" smallint,
	"registration_number" text,
	"medical_council" text,
	"registration_verified_at" timestamp with time zone,
	"bio" text,
	"languages" text[] DEFAULT '{}' NOT NULL,
	"clinical_focus" text[] DEFAULT '{}' NOT NULL,
	"education" jsonb DEFAULT '[]'::jsonb NOT NULL,
	"awards" jsonb DEFAULT '[]'::jsonb NOT NULL,
	"work_history" jsonb DEFAULT '[]'::jsonb NOT NULL,
	"status" "publish_status" DEFAULT 'draft' NOT NULL,
	"meta_title" text,
	"meta_description" text,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "doctors_slug_unique" UNIQUE("slug"),
	CONSTRAINT "doctors_slug_format" CHECK ("doctors"."slug" ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
	CONSTRAINT "doctors_practice_since_range" CHECK ("doctors"."practice_since" >= 1950),
	CONSTRAINT "doctors_published_requires_verified_registration" CHECK ("doctors"."status" <> 'published' or ("doctors"."registration_number" is not null and "doctors"."medical_council" is not null and "doctors"."registration_verified_at" is not null))
);
--> statement-breakpoint
CREATE TABLE "hospital_internal" (
	"hospital_id" uuid PRIMARY KEY NOT NULL,
	"mou_status" "mou_status" DEFAULT 'none' NOT NULL,
	"mou_signed_on" date,
	"mou_expires_on" date,
	"facilitation_terms" text,
	"international_desk_email" text,
	"international_desk_phone" text,
	"notes" text,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "hospital_specialties" (
	"hospital_id" uuid NOT NULL,
	"specialty_id" uuid NOT NULL,
	CONSTRAINT "hospital_specialties_hospital_id_specialty_id_pk" PRIMARY KEY("hospital_id","specialty_id")
);
--> statement-breakpoint
CREATE TABLE "hospitals" (
	"id" uuid PRIMARY KEY DEFAULT uuidv7() NOT NULL,
	"slug" text NOT NULL,
	"name" text NOT NULL,
	"city_id" uuid NOT NULL,
	"facility_type" "facility_type" NOT NULL,
	"accreditations" "accreditation"[] DEFAULT '{}' NOT NULL,
	"established_year" smallint,
	"bed_count" integer,
	"icu_bed_count" integer,
	"operating_theatres" smallint,
	"address" text NOT NULL,
	"pincode" char(6),
	"latitude" double precision,
	"longitude" double precision,
	"airport_distance_km" smallint,
	"airport_travel_mins" smallint,
	"overview" text,
	"technologies" text[] DEFAULT '{}' NOT NULL,
	"amenities" jsonb DEFAULT '{}'::jsonb NOT NULL,
	"status" "publish_status" DEFAULT 'draft' NOT NULL,
	"meta_title" text,
	"meta_description" text,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "hospitals_slug_unique" UNIQUE("slug"),
	CONSTRAINT "hospitals_slug_format" CHECK ("hospitals"."slug" ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
	CONSTRAINT "hospitals_pincode_format" CHECK ("hospitals"."pincode" ~ '^[1-9][0-9]{5}$'),
	CONSTRAINT "hospitals_established_year_range" CHECK ("hospitals"."established_year" >= 1800),
	CONSTRAINT "hospitals_capacity_non_negative" CHECK ("hospitals"."bed_count" >= 0 and "hospitals"."icu_bed_count" >= 0 and "hospitals"."operating_theatres" >= 0),
	CONSTRAINT "hospitals_coordinates_range" CHECK ("hospitals"."latitude" between -90 and 90 and "hospitals"."longitude" between -180 and 180)
);
--> statement-breakpoint
ALTER TABLE "doctor_hospitals" ADD CONSTRAINT "doctor_hospitals_doctor_id_doctors_id_fk" FOREIGN KEY ("doctor_id") REFERENCES "public"."doctors"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "doctor_hospitals" ADD CONSTRAINT "doctor_hospitals_hospital_id_hospitals_id_fk" FOREIGN KEY ("hospital_id") REFERENCES "public"."hospitals"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "doctor_internal" ADD CONSTRAINT "doctor_internal_doctor_id_doctors_id_fk" FOREIGN KEY ("doctor_id") REFERENCES "public"."doctors"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "doctors" ADD CONSTRAINT "doctors_primary_specialty_id_specialties_id_fk" FOREIGN KEY ("primary_specialty_id") REFERENCES "public"."specialties"("id") ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "hospital_internal" ADD CONSTRAINT "hospital_internal_hospital_id_hospitals_id_fk" FOREIGN KEY ("hospital_id") REFERENCES "public"."hospitals"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "hospital_specialties" ADD CONSTRAINT "hospital_specialties_hospital_id_hospitals_id_fk" FOREIGN KEY ("hospital_id") REFERENCES "public"."hospitals"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "hospital_specialties" ADD CONSTRAINT "hospital_specialties_specialty_id_specialties_id_fk" FOREIGN KEY ("specialty_id") REFERENCES "public"."specialties"("id") ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "hospitals" ADD CONSTRAINT "hospitals_city_id_cities_id_fk" FOREIGN KEY ("city_id") REFERENCES "public"."cities"("id") ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
CREATE INDEX "doctor_hospitals_hospital_id_index" ON "doctor_hospitals" USING btree ("hospital_id");--> statement-breakpoint
CREATE UNIQUE INDEX "doctor_hospitals_one_primary" ON "doctor_hospitals" USING btree ("doctor_id") WHERE "doctor_hospitals"."is_primary";--> statement-breakpoint
CREATE INDEX "doctors_primary_specialty_id_index" ON "doctors" USING btree ("primary_specialty_id");--> statement-breakpoint
CREATE INDEX "hospital_specialties_specialty_id_index" ON "hospital_specialties" USING btree ("specialty_id");--> statement-breakpoint
CREATE INDEX "hospitals_city_id_index" ON "hospitals" USING btree ("city_id");