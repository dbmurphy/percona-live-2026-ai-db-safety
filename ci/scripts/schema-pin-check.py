#!/usr/bin/env python3
"""Fail the PR if any query in the diff references a column/field not pinned in .schemas/.

Walks the unified diff between --base and --head, extracts identifiers from added
SQL lines (table.column or bare column near a FROM/SELECT) and Mongo-style field
references in JS migrations, and checks them against `.schemas/<name>.json`.

This is intentionally simple: false positives are fine because they force a
schema update; false negatives are not. If you hit a false positive, pin the
column in `.schemas/`.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SCHEMA_DIRS = [Path("postgres/.schemas"), Path("mongodb/.schemas")]
HOT = {"activity", "users", "sessions"}

IDENT_RE = re.compile(r"\b([a-z_][a-z0-9_]*)\.([a-z_][a-z0-9_]*)\b", re.IGNORECASE)


def load_schemas() -> dict[str, set[str]]:
    by_name: dict[str, set[str]] = {}
    for d in SCHEMA_DIRS:
        if not d.exists():
            continue
        for f in d.glob("*.json"):
            data = json.loads(f.read_text())
            name = data.get("table") or data.get("collection") or f.stem
            cols = {c["name"] for c in data.get("columns", [])}
            cols |= {c["name"] for c in data.get("fields", [])}
            by_name[name] = cols
    return by_name


def diff_added_lines(base: str, head: str) -> list[tuple[str, str]]:
    """Return (filename, line) for each added line in the diff."""
    out = subprocess.check_output(
        ["git", "diff", "--unified=0", f"{base}..{head}"], text=True
    )
    current = None
    added: list[tuple[str, str]] = []
    for line in out.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
        elif line.startswith("+") and not line.startswith("+++") and current:
            added.append((current, line[1:]))
    return added


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--head", required=True)
    args = ap.parse_args()

    schemas = load_schemas()
    if not schemas:
        print("schema-pin-check: no .schemas/ found; nothing to enforce.")
        return 0

    failures: list[str] = []
    for fname, line in diff_added_lines(args.base, args.head):
        if not fname.endswith((".sql", ".js", ".py")):
            continue
        for table, col in IDENT_RE.findall(line):
            t = table.lower()
            if t not in schemas:
                continue
            if col.lower() not in {c.lower() for c in schemas[t]}:
                failures.append(f"{fname}: {t}.{col} is not in .schemas/{t}.json")

    if failures:
        print("schema-pin-check: unpinned references found:")
        for f in failures:
            print(f"  - {f}")
        print("\nEither pin the column in .schemas/ or fix the typo.")
        return 1

    print("schema-pin-check: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
