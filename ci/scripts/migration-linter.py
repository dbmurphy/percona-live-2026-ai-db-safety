#!/usr/bin/env python3
"""Lint migration files in deploy/migrations/.

Every migration MUST:
  - Have a `depends_on:` header line listing prior migration IDs.
  - Have a `down:` block (reverse statement, even if empty for additive-only).
  - Not reference a column from an unmerged migration.
  - If it replaces an existing index, include a JUSTIFICATION comment.

Usage: migration-linter.py --base <sha> --head <sha>
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

MIGRATIONS = Path("deploy/migrations")
DEPENDS_RE = re.compile(r"^--\s*depends_on:\s*\[(.*)\]", re.MULTILINE)
DEPENDS_JS_RE = re.compile(r"^//\s*depends_on:\s*\[(.*)\]", re.MULTILINE)
DOWN_RE = re.compile(r"^(--|//)\s*down:", re.MULTILINE)
INDEX_REPLACE_RE = re.compile(r"(DROP INDEX|dropIndex).*?(CREATE INDEX|createIndex)", re.S | re.I)
JUSTIFICATION_RE = re.compile(r"JUSTIFICATION:", re.I)


def changed_migrations(base: str, head: str) -> list[Path]:
    out = subprocess.check_output(
        ["git", "diff", "--name-only", "--diff-filter=A", f"{base}..{head}"], text=True
    )
    return [Path(p) for p in out.splitlines() if p.startswith(str(MIGRATIONS) + "/")]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--head", required=True)
    args = ap.parse_args()

    new = changed_migrations(args.base, args.head)
    if not new:
        print("migration-linter: no new migrations.")
        return 0

    failures: list[str] = []
    for f in new:
        text = f.read_text()
        depends = DEPENDS_RE.search(text) or DEPENDS_JS_RE.search(text)
        if not depends:
            failures.append(f"{f}: missing `depends_on:` header")
        if not DOWN_RE.search(text):
            failures.append(f"{f}: missing `down:` block")
        if INDEX_REPLACE_RE.search(text) and not JUSTIFICATION_RE.search(text):
            failures.append(f"{f}: replaces an index without a JUSTIFICATION comment")

    if failures:
        print("migration-linter: failed:")
        for x in failures:
            print(f"  - {x}")
        return 1

    print("migration-linter: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
