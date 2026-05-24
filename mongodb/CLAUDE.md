# MongoDB assistant rules

These rules are non-negotiable for any database work in this project.

## 1. explain() before aggregations on hot collections

Hot collections: `activity`, `users`, `sessions`.

Before running any `find` or `aggregate` against a hot collection:

```js
db.<coll>.explain("executionStats").aggregate(<pipeline>)
```

Abort if `totalDocsExamined / nReturned > 1000`. Abort if the winning plan is `COLLSCAN`. See `.claude/skills/explain-first.md`.

## 2. Verify field names against pinned schemas

Read `.schemas/<collection>.json` before referencing any field. MongoDB has no DDL safety net — a typo like `userid` vs `user_id` produces a silent empty result. See `.claude/skills/schema-pin.md`.

## 3. Index changes are migrations

Never call `createIndex` or `dropIndex` from the assistant. Emit a migration in `deploy/migrations/` with both `up` and `down` and a `depends_on:` header. See `.claude/skills/index-change-guard.md`.

## 4. Aggregations must start with $match

Any pipeline against a hot collection that does not start with `$match` on an indexed field is unbounded and will be blocked by the hook. `$sort`/`$group`/`$lookup` first means a collection scan first.

## 5. $lookup foreignField must be indexed

`$lookup` without an index on `foreignField` is a nested loop join over the foreign collection per source document. Check `.schemas/<foreign>.json` indexes before writing the stage.

## 6. No writes from this assistant

The MCP server is started with `--readOnly` against a `read`-only user. `$out`, `$merge`, `$function`, `createIndex`, `dropIndex` are blocked at the hook regardless.
