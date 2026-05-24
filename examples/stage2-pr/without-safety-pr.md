# Stage 2 — PR, without safety

**Title:** Add archive endpoint

**Diff:**

```diff
+ def list_archived(user_id):
+     return db.activity.find({"userid": user_id, "archived": True}).sort("ts", -1)
```

**Reviewer comment (30 seconds later):** LGTM 🚀

Merged.

In production, every request hits `COLLSCAN` on the 300M-document collection because:

1. `userid` isn't a field. It's `user_id`.
2. The query returns nothing regardless, so caller logs say "no archives" forever.
3. The COLLSCAN holds the read worker for the duration of the operation timeout. Latency p99 doubles.

The on-call sees the latency alert at 02:00. Reverting takes another deploy.
