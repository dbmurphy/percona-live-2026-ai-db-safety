# Your LLM Will Drop That Table

Companion repo for the Percona Live 2026 talk **"Your LLM Will Drop That Table: Making AI-Assisted Database Work Safe"** by David Murphy (Senior Database Engineer, Motion).

## The thesis

AI coding assistants connected to dev databases will:

1. Generate unbounded scans on huge collections.
2. Write joins / `$lookup` without index coverage.
3. Emit migrations that destroy data when run out of order.

The fix is **not** prompting better. The fix is pinning the AI to a permission floor (a read-only DB user) and enforcing one rule at three stages — IDE, PR, Deploy:

> **No query reaches the database without proving its cost first.**

This repo demonstrates that floor and those three gates for both **MongoDB** and **Postgres**.

## Layout

- `postgres/` — read-only role, MCP config, CLAUDE.md, skills, hooks, pinned schemas.
- `mongodb/` — same shape, adapted to Mongo terms.
- `ci/` — PR-stage gates: schema-pin check, EXPLAIN bot, migration linter.
- `deploy/` — dependency-ordered migration runner and pre-deploy checks.
- `examples/` — bad-vs-good replays at each of the three stages.
- `deck/` — placeholder for the talk's `.pptx`.

## Quick start

Pick your database and follow its README:

- [postgres/README.md](postgres/README.md)
- [mongodb/README.md](mongodb/README.md)

Then walk the CI and deploy stages:

- [ci/README.md](ci/README.md)
- [deploy/README.md](deploy/README.md)

## Talk link

Session page: see Percona Live 2026 schedule. Slides are in `deck/` once published.

## License

MIT — see [LICENSE](LICENSE).
