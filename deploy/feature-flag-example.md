# Feature-flag the write path

New write paths reach one shard or one tenant first. Never the whole fleet.

## Pattern

```python
if flag("new_archive_writer", tenant_id=ctx.tenant_id):
    archive_v2.write(record)
else:
    archive_v1.write(record)
```

Ramp:

1. Internal tenants only — 1 day.
2. 1% of customer tenants — 2 days.
3. 10% — 2 days.
4. 100%.

At each step: confirm error rate and write latency p99 are flat in Datadog before advancing. If they're not, flip the flag back instantly — the old path is still live.

## Why

A bad migration is recoverable. A bad write path that has been silently corrupting 100% of rows for an hour is not. The flag is the off-switch the migration can't be.
