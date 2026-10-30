-- DPDP Rule 6: audit logs are append-only and kept for at least one year.
CREATE FUNCTION audit_logs_guard() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'TRUNCATE' THEN
    RAISE EXCEPTION 'audit_logs cannot be truncated';
  ELSIF TG_OP = 'UPDATE' THEN
    RAISE EXCEPTION 'audit_logs is append-only';
  ELSIF OLD.occurred_at > now() - interval '1 year' THEN
    RAISE EXCEPTION 'audit_logs rows must be kept for at least one year';
  END IF;
  RETURN OLD;
END;
$$;
--> statement-breakpoint
CREATE TRIGGER audit_logs_guard_rows
  BEFORE UPDATE OR DELETE ON audit_logs
  FOR EACH ROW EXECUTE FUNCTION audit_logs_guard();
--> statement-breakpoint
CREATE TRIGGER audit_logs_guard_truncate
  BEFORE TRUNCATE ON audit_logs
  FOR EACH STATEMENT EXECUTE FUNCTION audit_logs_guard();
