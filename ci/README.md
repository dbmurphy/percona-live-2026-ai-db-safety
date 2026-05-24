# PR-stage gates

Three workflows, all required to merge:

1. **schema-pin-check** — fails if any query in the diff references a field not in `.schemas/`.
2. **explain-bot** — spins up a shadow DB with the `.schemas/` structure and synthetic data shaped like prod, runs `EXPLAIN` / `explain()` on every new query, posts results as a PR comment, fails if `rows_examined / rows_returned > 1000`.
3. **migration-linter** — every migration must have a `down`, a `depends_on:` header, and may not reference a column from an unmerged migration.

These are the second floor. Even if the IDE-stage hook is bypassed (commented-out, hostile contributor, hook didn't fire), the PR cannot merge without passing these.
