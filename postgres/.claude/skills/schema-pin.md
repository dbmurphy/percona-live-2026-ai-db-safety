---
name: schema-pin
description: Read the pinned schema for a Postgres table before referencing any of its columns. Prevents hallucinated field names that produce silent empty result sets.
---

# Schema pin

Before writing any query against a table in `.schemas/`, you MUST:

1. Read `.schemas/<table>.json`.
2. Confirm every column you reference appears in `columns[].name`.
3. Confirm the column's type matches your intended comparison (don't compare `bigint` to a string literal).
4. Note which indexes exist — your query plan should use one of them.

If a column you need is not in the pinned schema, STOP. Ask the human whether the schema is stale or whether the column genuinely does not exist. Do not run `\d` and silently update your mental model — the pinned schema is the source of truth that survives across sessions.

## Why

LLMs invent plausible column names (`created_at` when the column is `inserted_at`, `user_id` when it's `userId`). These produce queries that parse fine and return zero rows, which then get pasted into a PR. The pinned schema is the cheapest possible cure.
