---
name: index-change-guard
description: Never run CREATE INDEX or DROP INDEX directly. Emit a migration file with up + down + depends_on header.
---

# Index change guard

If you decide an index would help, you MUST NOT issue `CREATE INDEX` against the database. Instead:

1. Create a file in `deploy/migrations/` named `YYYY_MM_DD_<slug>.sql`.
2. Include header:

   ```sql
   -- depends_on: [<latest migration id>]
   -- down:
   -- DROP INDEX CONCURRENTLY IF EXISTS <name>;
   ```

3. Write the `up` as `CREATE INDEX CONCURRENTLY` — never block writes on a hot table.
4. Quote, in your response, the EXPLAIN plan before and the EXPLAIN plan after (simulated against a shadow database in CI).
5. Stop. The migration runs through the deploy stage, not from the assistant.

## Why

`CREATE INDEX` without `CONCURRENTLY` takes an `AccessExclusiveLock` and stalls every writer to the table. `DROP INDEX` issued by an assistant in a dev session is how the same index gets re-added in three different PRs. Migrations make index churn visible.
