---
name: index-change-guard
description: Never call createIndex or dropIndex from the assistant. Emit a migration with up + down + depends_on header.
---

# Index change guard

If you decide an index would help:

1. Create a file in `deploy/migrations/` named `YYYY_MM_DD_<slug>.js`.
2. Header:

   ```js
   // depends_on: [<latest migration id>]
   // down:
   // db.<coll>.dropIndex("<name>");
   ```

3. Write `up` as `db.<coll>.createIndex({...}, { background: true, name: "<name>" })`. Always name the index.
4. Quote the `explain()` plan before and after (simulated against a shadow database in CI).
5. Stop. The migration runs through the deploy stage.

## Why

Mongo silently lets you create three near-duplicate indexes on the same collection. Each one costs write throughput. Routing index changes through migrations makes the index set a reviewed artifact instead of session debris.
