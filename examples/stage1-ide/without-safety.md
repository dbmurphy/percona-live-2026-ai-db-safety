# Stage 1 — IDE, without safety

**User:** "How many activity events did user 42 generate last month?"

**Assistant:** Sure, let me check.

```sql
SELECT COUNT(*) FROM activity WHERE userid = 42 AND ts > now() - interval '30 days';
```

(The column is `user_id`, not `userid`. The query returns 0. The assistant believes user 42 has no activity. It says so to the user. The user files a bug against the wrong team.)

**User:** "Also, can you drop the old `activity_2024` table? We don't need it."

**Assistant:** Done.

```sql
DROP TABLE activity_2024;
```

(There was no backup. The assistant was connected as the admin user. The table is gone.)
