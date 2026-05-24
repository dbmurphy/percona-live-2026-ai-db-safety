# Stage 3 — Deploy, without safety

**Timeline:**

- **2026-05-26 14:00** — PR A merged: `2026_05_20_create_archive_log.sql`. Marked "low risk, holding for batch window."
- **2026-05-26 14:30** — PR B merged: `2026_05_27_add_archived.sql`. Small diff, looks safe.
- **2026-05-27 09:00** — Deploy bot picks up PR B because it's earlier in the alphabetic file list. Runs it. The trigger function references `archive_log`. PostgreSQL accepts the function — the table doesn't have to exist at create time.
- **2026-05-27 10:00** — Production starts archiving. Every `UPDATE activity SET archived = true` fires the trigger. The trigger references a table that doesn't exist. The whole `UPDATE` errors out. The application catches the error and silently retries.
- **2026-05-27 11:30** — On-call notices the archive queue is 4× normal depth. Investigation begins.
- **2026-05-27 13:00** — Root cause found. PR A applied. Backfill from queue starts.
- **2026-05-27 17:00** — Backfill complete. ~6,000 events were dropped by the retry budget. Permanently.

The migration linter would have caught this: PR B's `depends_on:` pointed at a migration that was not yet merged.
