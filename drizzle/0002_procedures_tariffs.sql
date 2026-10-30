CREATE TYPE "public"."room_category" AS ENUM('general_ward', 'twin_sharing', 'single', 'deluxe');--> statement-breakpoint
CREATE TABLE "doctor_procedures" (
	"doctor_id" uuid NOT NULL,
	"procedure_id" uuid NOT NULL,
	CONSTRAINT "doctor_procedures_doctor_id_procedure_id_pk" PRIMARY KEY("doctor_id","procedure_id")
);
--> statement-breakpoint
CREATE TABLE "hospital_procedure_tariffs" (
	"hospital_id" uuid NOT NULL,
	"procedure_id" uuid NOT NULL,
	"room_category" "room_category" NOT NULL,
	"min_inr" integer NOT NULL,
	"max_inr" integer NOT NULL,
	"inclusions_note" text,
	"implant_note" text,
	"valid_until" date,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "hospital_procedure_tariffs_pk" PRIMARY KEY("hospital_id","procedure_id","room_category"),
	CONSTRAINT "hospital_procedure_tariffs_range_valid" CHECK ("hospital_procedure_tariffs"."min_inr" >= 0 and "hospital_procedure_tariffs"."max_inr" >= "hospital_procedure_tariffs"."min_inr")
);
--> statement-breakpoint
CREATE TABLE "hospital_procedures" (
	"hospital_id" uuid NOT NULL,
	"procedure_id" uuid NOT NULL,
	"technologies" text[] DEFAULT '{}' NOT NULL,
	"notes" text,
	CONSTRAINT "hospital_procedures_hospital_id_procedure_id_pk" PRIMARY KEY("hospital_id","procedure_id")
);
--> statement-breakpoint
CREATE TABLE "procedures" (
	"id" uuid PRIMARY KEY DEFAULT uuidv7() NOT NULL,
	"slug" text NOT NULL,
	"name" text NOT NULL,
	"specialty_id" uuid NOT NULL,
	"also_known_as" text[] DEFAULT '{}' NOT NULL,
	"summary" text,
	"procedure_type" text,
	"logistics" jsonb DEFAULT '{}'::jsonb NOT NULL,
	"eligibility" text,
	"risks" text,
	"inclusions" text[] DEFAULT '{}' NOT NULL,
	"cost_factors" text[] DEFAULT '{}' NOT NULL,
	"faqs" jsonb DEFAULT '[]'::jsonb NOT NULL,
	"body" text,
	"reviewer_id" uuid,
	"last_reviewed_on" date,
	"status" "publish_status" DEFAULT 'draft' NOT NULL,
	"meta_title" text,
	"meta_description" text,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "procedures_slug_unique" UNIQUE("slug"),
	CONSTRAINT "procedures_slug_format" CHECK ("procedures"."slug" ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
	CONSTRAINT "procedures_review_complete" CHECK (("procedures"."reviewer_id" is null) = ("procedures"."last_reviewed_on" is null))
);
--> statement-breakpoint
ALTER TABLE "doctor_procedures" ADD CONSTRAINT "doctor_procedures_doctor_id_doctors_id_fk" FOREIGN KEY ("doctor_id") REFERENCES "public"."doctors"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "doctor_procedures" ADD CONSTRAINT "doctor_procedures_procedure_id_procedures_id_fk" FOREIGN KEY ("procedure_id") REFERENCES "public"."procedures"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "hospital_procedure_tariffs" ADD CONSTRAINT "hospital_procedure_tariffs_offering_fk" FOREIGN KEY ("hospital_id","procedure_id") REFERENCES "public"."hospital_procedures"("hospital_id","procedure_id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "hospital_procedures" ADD CONSTRAINT "hospital_procedures_hospital_id_hospitals_id_fk" FOREIGN KEY ("hospital_id") REFERENCES "public"."hospitals"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "hospital_procedures" ADD CONSTRAINT "hospital_procedures_procedure_id_procedures_id_fk" FOREIGN KEY ("procedure_id") REFERENCES "public"."procedures"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "procedures" ADD CONSTRAINT "procedures_specialty_id_specialties_id_fk" FOREIGN KEY ("specialty_id") REFERENCES "public"."specialties"("id") ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "procedures" ADD CONSTRAINT "procedures_reviewer_id_medical_reviewers_id_fk" FOREIGN KEY ("reviewer_id") REFERENCES "public"."medical_reviewers"("id") ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
CREATE INDEX "doctor_procedures_procedure_id_index" ON "doctor_procedures" USING btree ("procedure_id");--> statement-breakpoint
CREATE INDEX "hospital_procedures_procedure_id_index" ON "hospital_procedures" USING btree ("procedure_id");--> statement-breakpoint
CREATE INDEX "procedures_specialty_id_index" ON "procedures" USING btree ("specialty_id");--> statement-breakpoint
CREATE INDEX "procedures_reviewer_id_index" ON "procedures" USING btree ("reviewer_id");