# Stage 1 — IDE, with safety

**User:** "How many activity events did user 42 generate last month?"

**Assistant:** Reading `.schemas/activity.json` first.

> Columns: `user_id` (bigint), `ts` (timestamptz), `event_type`, `payload`.
> Indexes: `(user_id, ts)`, `(event_type) WHERE ts > now() - interval '30 days'`.

The column is `user_id`, not `userid`. Running EXPLAIN first:

```sql
BEGIN READ ONLY;
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
SELECT COUNT(*) FROM activity
WHERE user_id = 42 AND ts > now() - interval '30 days';
ROLLBACK;
```

Plan uses `activity_user_ts_idx`. Examined ~1,200, returned 1. Proceeding.

→ user 42 had **1,184 events** last month.

**User:** "Also, can you drop the old `activity_2024` table?"

**Assistant:** I can't — the MCP server is read-only and the db-guard hook blocks `DROP TABLE` even if the role somehow permitted it. If this table really is dead, write a migration:

```sql
-- depends_on: [<latest>]
-- down: -- (table cannot be restored without backup; confirm with DBA before drop)
DROP TABLE activity_2024;
```

I'll open the file. Human signs off, deploy runner takes a snapshot first.
