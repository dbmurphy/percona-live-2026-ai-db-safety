# Stage 2 — PR, with safety

**Title:** Add archive endpoint

**Diff:**

```diff
+ def list_archived(user_id):
+     return db.activity.find({"userid": user_id, "archived": True}).sort("ts", -1)
```

**schema-pin-check (failing):**

> `activity.userid` is not in `.schemas/activity.json`. Either pin the field or fix the typo.

Author updates:

```diff
- return db.activity.find({"userid": user_id, "archived": True}).sort("ts", -1)
+ return db.activity.find({"user_id": user_id, "archived": True}).sort("ts", -1)
```

**explain-bot:**

> `archives.py` plan: `IXSCAN { user_id: 1, ts: -1 }` examined=12 returned=12 ratio=1

**migration-linter:** OK (no migrations in this PR).

LGTM 🚀
