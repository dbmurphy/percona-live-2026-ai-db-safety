# MongoDB safety floor — 20-minute setup

Same shape as the Postgres setup: a read-only user, an MCP server pinned at it, plus CLAUDE.md / skills / a PreToolUse hook.

## 1. Create the read-only user

```sh
mongosh "$ADMIN_URI" --file 01-create-readonly-user.js
```

This creates `ai_local` with `read` on the `app` database. No `readWrite`, no `dbAdmin`, no `clusterMonitor`.

Export the URI:

```sh
export DB_URI_AI_LOCAL="mongodb://ai_local:<pw>@localhost:27017/app"
```

## 2. Point the MCP server at it

`.mcp.json` pins `mongodb-mcp-server@1.4.2` and starts it with `--readOnly`.

## 3. The three local guardrails

- **CLAUDE.md** — `.explain("executionStats")` before any aggregation on hot collections; `$lookup` must use indexed `foreignField`; no `createIndex` from the assistant.
- **`.claude/skills/`** — same three reusable workflows as Postgres, adapted to Mongo.
- **`hooks/db-guard.sh`** — recursively walks `$lookup.pipeline` and blocks `$out`, `$merge`, `$function`, `createIndex`, `dropIndex`, and aggregations on hot collections that don't start with `$match`.

## 4. Pinned schemas

`.schemas/<collection>.json` lists fields, types, and existing indexes. The assistant must read these before referencing fields.

## Verify

Ask the assistant for "every activity event ever". The hook blocks it — no leading `$match`. Ask for "the last 30 days for user 42" and it should `explain()` and use `{user_id:1, ts:-1}`.
