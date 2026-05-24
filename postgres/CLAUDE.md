# Postgres assistant rules

These rules are non-negotiable for any database work in this project. They exist because LLMs reliably produce unbounded scans and out-of-order migrations when left unguided.

## 1. EXPLAIN before SELECT on hot tables

Hot tables: `activity`, `users`, `sessions`.

Before issuing any `SELECT` against a hot table, wrap it:

```sql
BEGIN READ ONLY;
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) <the query>;
ROLLBACK;
```

Abort the query if `Rows Returned / Rows Examined < 0.01` or estimated cost suggests a seq scan over a hot table. See `.claude/skills/explain-first.md`.

## 2. Verify field names against pinned schemas

Before referencing any column on a hot table, read `.schemas/<table>.json`. Do not invent columns. If a column you need is not in the schema, stop and ask. See `.claude/skills/schema-pin.md`.

## 3. Index changes are migrations, not queries

Never issue `CREATE INDEX` or `DROP INDEX` directly. Emit a migration file in `deploy/migrations/` with both `up` and `down` and a `depends_on:` header. See `.claude/skills/index-change-guard.md`.

## 4. Migrations require dependency headers

Every file in `deploy/migrations/` begins with:

```sql
-- depends_on: [<prior migration id>, ...]
-- down:
-- <reverse statement>
```

The deploy runner refuses to apply a migration before its dependencies.

## 5. No writes from this assistant

The MCP server is started with `--readOnly` against a `pg_read_all_data` role. If you find yourself wanting to write, you are wrong about what you are doing — switch to producing a migration file for human review.
