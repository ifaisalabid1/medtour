CREATE TYPE "public"."actor_type" AS ENUM('staff', 'patient', 'system');--> statement-breakpoint
CREATE TYPE "public"."document_kind" AS ENUM('medical_report', 'prescription', 'passport', 'other');--> statement-breakpoint
CREATE TYPE "public"."lead_intent" AS ENUM('treatment', 'second_opinion', 'teleconsult', 'medical_visa', 'other');--> statement-breakpoint
CREATE TYPE "public"."lead_status" AS ENUM('new', 'contacted', 'awaiting_documents', 'under_review', 'quote_sent', 'converted', 'closed', 'spam');--> statement-breakpoint
CREATE TYPE "public"."reports_status" AS ENUM('has_reports', 'no_reports', 'wants_tests_in_india');--> statement-breakpoint
CREATE TYPE "public"."travel_timeline" AS ENUM('within_1_month', 'in_1_3_months', 'in_3_6_months', 'in_6_12_months', 'not_decided', 'no_travel');--> statement-breakpoint
CREATE TABLE "audit_logs" (
	"id" bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY (sequence name "audit_logs_id_seq" INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START WITH 1 CACHE 1),
	"occurred_at" timestamp with time zone DEFAULT now() NOT NULL,
	"actor_type" "actor_type" NOT NULL,
	"actor_id" text,
	"action" text NOT NULL,
	"entity_type" text,
	"entity_id" text,
	"lead_id" uuid,
	"ip_address" "inet",
	"user_agent" text,
	"metadata" jsonb DEFAULT '{}'::jsonb NOT NULL
);
--> statement-breakpoint
CREATE TABLE "consent_records" (
	"id" uuid PRIMARY KEY DEFAULT uuidv7() NOT NULL,
	"lead_id" uuid NOT NULL,
	"notice_version" text NOT NULL,
	"notice_sha256" char(64) NOT NULL,
	"purposes" text[] NOT NULL,
	"granted_at" timestamp with time zone DEFAULT now() NOT NULL,
	"withdrawn_at" timestamp with time zone,
	"ip_address" "inet",
	"user_agent" text,
	CONSTRAINT "consent_records_withdrawn_after_granted" CHECK ("consent_records"."withdrawn_at" >= "consent_records"."granted_at"),
	CONSTRAINT "consent_records_has_purposes" CHECK (cardinality("consent_records"."purposes") > 0)
);
--> statement-breakpoint
CREATE TABLE "patient_documents" (
	"id" uuid PRIMARY KEY DEFAULT uuidv7() NOT NULL,
	"lead_id" uuid NOT NULL,
	"kind" "document_kind" NOT NULL,
	"object_key" text NOT NULL,
	"original_filename" text NOT NULL,
	"mime_type" text NOT NULL,
	"size_bytes" integer NOT NULL,
	"uploaded_at" timestamp with time zone,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "patient_documents_objectKey_unique" UNIQUE("object_key"),
	CONSTRAINT "patient_documents_size_positive" CHECK ("patient_documents"."size_bytes" > 0)
);
--> statement-breakpoint
CREATE TABLE "patient_leads" (
	"id" uuid PRIMARY KEY DEFAULT uuidv7() NOT NULL,
	"ref_no" integer GENERATED ALWAYS AS IDENTITY (sequence name "patient_leads_ref_no_seq" INCREMENT BY 1 MINVALUE 1 MAXVALUE 2147483647 START WITH 1001 CACHE 1),
	"full_name" text,
	"email" text,
	"phone" text,
	"description" text,
	"country_code" char(2) NOT NULL,
	"indian_state" text,
	"passport_country" char(2),
	"intent" "lead_intent" NOT NULL,
	"reports_status" "reports_status",
	"travel_timeline" "travel_timeline",
	"needs_visa_letter" boolean DEFAULT false NOT NULL,
	"open_to_paid_teleconsult" boolean DEFAULT false NOT NULL,
	"needs_insurance_help" boolean DEFAULT false NOT NULL,
	"procedure_id" uuid,
	"hospital_id" uuid,
	"doctor_id" uuid,
	"source_path" text,
	"utm" jsonb DEFAULT '{}'::jsonb NOT NULL,
	"status" "lead_status" DEFAULT 'new' NOT NULL,
	"anonymized_at" timestamp with time zone,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "patient_leads_refNo_unique" UNIQUE("ref_no"),
	CONSTRAINT "patient_leads_pii_present" CHECK ("patient_leads"."anonymized_at" is not null or ("patient_leads"."full_name" is not null and "patient_leads"."email" is not null and "patient_leads"."phone" is not null and "patient_leads"."description" is not null)),
	CONSTRAINT "patient_leads_phone_e164" CHECK ("patient_leads"."phone" ~ '^\+[1-9][0-9]{6,14}$'),
	CONSTRAINT "patient_leads_country_code_format" CHECK ("patient_leads"."country_code" ~ '^[A-Z]{2}$' and "patient_leads"."passport_country" ~ '^[A-Z]{2}$'),
	CONSTRAINT "patient_leads_domestic_has_state" CHECK ("patient_leads"."country_code" <> 'IN' or "patient_leads"."indian_state" is not null)
);
--> statement-breakpoint
ALTER TABLE "consent_records" ADD CONSTRAINT "consent_records_lead_id_patient_leads_id_fk" FOREIGN KEY ("lead_id") REFERENCES "public"."patient_leads"("id") ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "patient_documents" ADD CONSTRAINT "patient_documents_lead_id_patient_leads_id_fk" FOREIGN KEY ("lead_id") REFERENCES "public"."patient_leads"("id") ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "patient_leads" ADD CONSTRAINT "patient_leads_procedure_id_procedures_id_fk" FOREIGN KEY ("procedure_id") REFERENCES "public"."procedures"("id") ON DELETE set null ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "patient_leads" ADD CONSTRAINT "patient_leads_hospital_id_hospitals_id_fk" FOREIGN KEY ("hospital_id") REFERENCES "public"."hospitals"("id") ON DELETE set null ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "patient_leads" ADD CONSTRAINT "patient_leads_doctor_id_doctors_id_fk" FOREIGN KEY ("doctor_id") REFERENCES "public"."doctors"("id") ON DELETE set null ON UPDATE no action;--> statement-breakpoint
CREATE INDEX "audit_logs_occurred_at_index" ON "audit_logs" USING btree ("occurred_at");--> statement-breakpoint
CREATE INDEX "audit_logs_lead_id_index" ON "audit_logs" USING btree ("lead_id");--> statement-breakpoint
CREATE INDEX "audit_logs_actor_id_index" ON "audit_logs" USING btree ("actor_id");--> statement-breakpoint
CREATE INDEX "consent_records_lead_id_index" ON "consent_records" USING btree ("lead_id");--> statement-breakpoint
CREATE INDEX "patient_documents_lead_id_index" ON "patient_documents" USING btree ("lead_id");--> statement-breakpoint
CREATE INDEX "patient_leads_status_created_at_index" ON "patient_leads" USING btree ("status","created_at");--> statement-breakpoint
CREATE INDEX "patient_leads_email_index" ON "patient_leads" USING btree ("email");--> statement-breakpoint
CREATE INDEX "patient_leads_phone_index" ON "patient_leads" USING btree ("phone");