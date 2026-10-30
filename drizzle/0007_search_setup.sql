-- Fuzzy matching for typos ("cardiolgy", "appolo"). pg_trgm is a trusted extension:
-- the database owner can enable it without superuser rights.
CREATE EXTENSION IF NOT EXISTS pg_trgm;
--> statement-breakpoint
-- array_to_string is STABLE, but generated columns accept only IMMUTABLE functions.
-- Joining a text[] with spaces never depends on settings, so this wrapper is safe.
CREATE FUNCTION immutable_array_to_string(text[]) RETURNS text
LANGUAGE sql IMMUTABLE PARALLEL SAFE
RETURN array_to_string($1, ' ');
--> statement-breakpoint
-- `name <% query` matches when word similarity >= this threshold (default 0.6 misses "appolo").
DO $$
BEGIN
  EXECUTE format('ALTER DATABASE %I SET pg_trgm.word_similarity_threshold = 0.4', current_database());
END
$$;
