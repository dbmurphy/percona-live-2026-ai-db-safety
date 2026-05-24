---
name: schema-pin
description: Read the pinned schema for a Mongo collection before referencing any of its fields. Mongo has no DDL safety net — typos silently return zero documents.
---

# Schema pin

Before writing any query against a collection in `.schemas/`, you MUST:

1. Read `.schemas/<collection>.json`.
2. Confirm every field you reference appears in `fields[].name` (including dotted sub-paths).
3. Confirm the BSON type — comparing a `long` to a JS string returns nothing.
4. Note which indexes exist. Your `$match` should hit one.

If a field you need is not pinned, STOP. Ask whether the schema is stale or the field is genuinely absent. Do not run `db.coll.findOne()` to "discover" the shape — sample documents lie when the collection is polymorphic.

## Why

Mongo's flexible schema is the biggest LLM footgun. The assistant invents `userId`, the collection uses `user_id`, the query returns `[]`, the assistant says "no activity for this user", and a human ships that conclusion to a stakeholder. Pinning kills this class of bug.
