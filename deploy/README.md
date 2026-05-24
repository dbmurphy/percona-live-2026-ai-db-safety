# Deploy stage

Third floor under the assistant. The deploy runner:

1. Reads every migration's `depends_on:` header.
2. Topologically sorts them. Refuses to run B before A if B depends on A.
3. For destructive migrations (`DROP TABLE`, `DROP COLUMN`, `$unset`), takes a snapshot first, runs `down` against a staging snapshot to verify rollback works, and waits for a one-click human confirmation.

## Files

- `migrate.py` — the runner.
- `pre-deploy-checks.sh` — destructive-statement detector and snapshot trigger.
- `feature-flag-example.md` — how to ramp new write paths to one shard or one tenant before everyone.
- `migrations/` — example migrations including the out-of-order pair from the talk.

## Why this exists

The 2026-05-27 incident: two PRs landed in the same week. `2026_05_27_add_archived.sql` was reviewed and shipped first because it was smaller. It referenced the `archive_log` table created in `2026_05_20_create_archive_log.sql`. The deploy ran the May 27 file alone, the trigger fired, and rows landed nowhere. We lost a day of writes.

`depends_on:` makes that physically impossible.
