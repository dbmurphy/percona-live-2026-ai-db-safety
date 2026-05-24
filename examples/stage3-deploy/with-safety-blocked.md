# Stage 3 — Deploy, with safety

```
$ python deploy/migrate.py --plan
  [ ] 2026_05_20_create_archive_log  depends_on=[]
  [ ] 2026_05_27_add_archived        depends_on=['2026_05_20_create_archive_log']

$ python deploy/migrate.py --apply
-- applying 2026_05_20_create_archive_log (2026_05_20_create_archive_log.sql)
-- applying 2026_05_27_add_archived (2026_05_27_add_archived.sql)
```

If only PR B had merged, migrate.py would say:

```
migrate: missing dependency 2026_05_20_create_archive_log
```

…and exit non-zero before touching the database. The deploy is blocked. The on-call wakes up at a normal hour.
