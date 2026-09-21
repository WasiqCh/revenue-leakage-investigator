-- ---------------------------------------------------------------------------
-- Runs once when the Postgres container is first created.
--
-- Plain-English: two jobs.
--   1. Turn on pgvector so we can store and search contract "meaning vectors".
--   2. Create a read-only database user. This is a real safety gate, not a
--      promise: the AI agent connects as rl_readonly, so it is literally
--      impossible for the agent to change an invoice, contract or price even
--      if it is tricked into trying. See docs/adr/ADR-004-read-only-role-guardrail.md
-- ---------------------------------------------------------------------------

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;   -- fuzzy text matching for entity resolution
CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- gen_random_uuid()

-- Read-only role used by the AI agent and by all detection/investigation code.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'rl_readonly') THEN
        CREATE ROLE rl_readonly LOGIN PASSWORD 'rl_readonly_pw';
    END IF;
END
$$;

-- Everything created later by Alembic migrations is automatically read-only
-- for rl_readonly. There is no "grant write" anywhere in this project.
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT ON TABLES TO rl_readonly;

-- The app role keeps full rights (it writes cases, evidence, decisions).
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL ON TABLES TO rl_app;
