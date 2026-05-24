---
name: explain-first
description: explain("executionStats") every aggregation against a hot Mongo collection. Abort COLLSCANs and >1000:1 examined-to-returned ratios.
---

# Explain first

Hot collections: `activity`, `users`, `sessions`. For ANY pipeline against these:

1. Run:

   ```js
   db.<coll>.explain("executionStats").aggregate(<pipeline>)
   ```

2. Parse `executionStats`. Compute `totalDocsExamined / nReturned`. If the ratio exceeds 1000, ABORT.

3. If `winningPlan.stage` is `COLLSCAN` (or `inputStage.stage` for piped plans), ABORT.

4. If a plan uses an index, quote the index name in your response.

## Why

A `db.activity.aggregate([{$group:...}])` over 300M documents will hit the operation timeout, return nothing useful, and pin a CPU core for the duration. The assistant doesn't feel that pain — the on-call engineer does. Explaining first makes the cost visible before the query runs.
