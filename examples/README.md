# Replays

Each subdirectory pairs a "without safety" failure with the same task done under the floor + gates.

- `stage1-ide/` — the assistant in the IDE, with and without the read-only user + hook.
- `stage2-pr/` — the same change as a PR, with and without explain-bot + migration-linter.
- `stage3-deploy/` — the out-of-order migration incident, with and without the dependency-ordered runner.
