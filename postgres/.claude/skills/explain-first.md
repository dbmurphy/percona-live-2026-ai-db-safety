---
name: explain-first
description: Wrap every query against a hot Postgres table in EXPLAIN ANALYZE inside a read-only transaction. Abort if the plan suggests an unbounded scan.
---

# Explain first

Hot tables: `activity`, `users`, `sessions`. For ANY query against these tables:

1. Run, in this exact form:

   ```sql
   BEGIN READ ONLY;
   EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) <the query>;
   ROLLBACK;
   ```

2. Parse the JSON plan. Compute `rows_examined / rows_returned`. If the ratio exceeds 1000, ABORT — the query is unbounded for the result it returns.

3. If the top node is `Seq Scan` on a hot table, ABORT regardless of cost.

4. If the plan uses an index, proceed. Quote the index name in your response so the human can audit it.

## Why

The first thing an LLM does against a 300M-row table is `SELECT * FROM activity WHERE user_id = 42` without checking whether `user_id` is indexed. That query runs for the full 5s statement timeout and returns nothing, then the assistant tries again with a different `WHERE`. Burning timeouts in a loop is how dev databases fall over.
