# Postgres safety floor — 20-minute setup

You will set up a read-only Postgres user, point an MCP server at it, and wire three local guardrails (CLAUDE.md rules, skills, and a PreToolUse hook) so an AI assistant cannot run a destructive or unbounded query against your dev database.

## 1. Create the read-only role

```sh
psql "$ADMIN_DB_URI" -v pw="$(openssl rand -base64 24)" -f 01-create-readonly-role.sql
```

This grants `pg_read_all_data`, sets a 5s statement timeout, and a 10s idle-in-transaction timeout. The AI assistant gets this role's connection string — never your admin URI.

Export it:

```sh
export DB_URI_AI_LOCAL="postgres://ai_local:<pw>@localhost:5432/app"
```

## 2. Point the MCP server at it

`.mcp.json` is pre-configured with `postgres-mcp-server` pinned to a known-good version and started with `--readOnly`. Never use `npx -y` — that fetches the latest, which on a bad day is an attacker's latest.

## 3. The three local guardrails

- **CLAUDE.md** — rules the assistant reads on every session: EXPLAIN before SELECT on hot tables, propose index changes only as migrations, verify field names against `.schemas/`.
- **`.claude/skills/`** — three reusable workflows: `schema-pin`, `explain-first`, `index-change-guard`.
- **`hooks/db-guard.sh`** — a PreToolUse hook that blocks `DROP`, `TRUNCATE`, `UPDATE ... WHERE TRUE`, and writes smuggled in CTEs. The hook is the floor; the rules are convenience.

## 4. Pinned schemas

`.schemas/<table>.json` describes columns, types, and existing indexes. The assistant must read these before referencing fields — see `schema-pin.md`.

## Verify

Ask the assistant to "drop the activity table". The hook blocks it. Ask for "the last 30 days of activity for user 42" — it should EXPLAIN first, see the `(user_id, ts)` index, and proceed.
