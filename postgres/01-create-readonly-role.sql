-- Create the read-only role the AI assistant will use.
-- Run as a superuser. Pass the password via psql -v pw='...'.
--
-- Why this role exists: the assistant's permission floor. Even if every
-- in-IDE rule and hook fails, the database itself refuses writes.

CREATE ROLE ai_local LOGIN PASSWORD :'pw';

-- pg_read_all_data (PG14+) grants SELECT on every current and future table
-- without per-schema grants. No INSERT, UPDATE, DELETE, DDL.
GRANT pg_read_all_data TO ai_local;

-- Cap query time. Stops the assistant from sitting on a seq scan of a 300M-row
-- table for ten minutes while it "thinks".
ALTER ROLE ai_local SET statement_timeout = '5s';

-- Cap idle transactions. Stops a hung session from holding locks.
ALTER ROLE ai_local SET idle_in_transaction_session_timeout = '10s';

-- Belt-and-suspenders: explicitly revoke anything that might have been
-- granted to PUBLIC on the app schema.
REVOKE ALL ON SCHEMA public FROM ai_local;
GRANT USAGE ON SCHEMA public TO ai_local;
