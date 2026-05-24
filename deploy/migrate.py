#!/usr/bin/env python3
"""Dependency-ordered migration runner.

Reads every file in deploy/migrations/, parses the `depends_on:` header,
topologically sorts, and applies in order. Refuses to apply a migration whose
dependencies have not been applied.

Usage:
  migrate.py --plan          # show order, don't run
  migrate.py --apply         # run pending migrations
  migrate.py --down <id>     # run the `down:` block of one migration
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

MIGRATIONS = Path(__file__).parent / "migrations"
APPLIED = Path(__file__).parent / ".applied"

ID_FROM_NAME = re.compile(r"^(\d{4}_\d{2}_\d{2}_[a-z0-9_]+)")
DEPENDS_RE = re.compile(r"^(?:--|//)\s*depends_on:\s*\[(.*?)\]", re.MULTILINE)
DOWN_RE = re.compile(r"^(?:--|//)\s*down:\s*\n(.*)", re.MULTILINE | re.DOTALL)


@dataclass
class Migration:
    id: str
    path: Path
    depends_on: list[str] = field(default_factory=list)
    text: str = ""


def parse_all() -> dict[str, Migration]:
    out: dict[str, Migration] = {}
    for f in sorted(MIGRATIONS.glob("*")):
        if f.suffix not in {".sql", ".js"}:
            continue
        m = ID_FROM_NAME.match(f.name)
        if not m:
            sys.exit(f"migrate: cannot parse id from {f.name}")
        mid = m.group(1)
        text = f.read_text()
        dep_match = DEPENDS_RE.search(text)
        if not dep_match:
            sys.exit(f"migrate: {f.name} has no depends_on header")
        deps_raw = dep_match.group(1).strip()
        deps = [d.strip() for d in deps_raw.split(",") if d.strip()]
        out[mid] = Migration(id=mid, path=f, depends_on=deps, text=text)
    return out


def topo_sort(migs: dict[str, Migration]) -> list[Migration]:
    ordered: list[Migration] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(mid: str) -> None:
        if mid in visited:
            return
        if mid in visiting:
            sys.exit(f"migrate: cycle involving {mid}")
        if mid not in migs:
            sys.exit(f"migrate: missing dependency {mid}")
        visiting.add(mid)
        for d in migs[mid].depends_on:
            visit(d)
        visiting.remove(mid)
        visited.add(mid)
        ordered.append(migs[mid])

    for mid in migs:
        visit(mid)
    return ordered


def applied() -> set[str]:
    if not APPLIED.exists():
        return set()
    return {line.strip() for line in APPLIED.read_text().splitlines() if line.strip()}


def record(mid: str) -> None:
    with APPLIED.open("a") as fh:
        fh.write(mid + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--down", metavar="ID")
    args = ap.parse_args()

    migs = parse_all()
    order = topo_sort(migs)
    done = applied()

    if args.plan:
        for m in order:
            mark = "✓" if m.id in done else " "
            print(f"  [{mark}] {m.id}  depends_on={m.depends_on or '[]'}")
        return 0

    if args.down:
        if args.down not in migs:
            sys.exit(f"migrate: unknown id {args.down}")
        m = migs[args.down]
        block = DOWN_RE.search(m.text)
        if not block:
            sys.exit(f"migrate: {m.id} has no down: block")
        print(f"-- would execute down for {m.id}:")
        print(block.group(1))
        return 0

    if args.apply:
        for m in order:
            if m.id in done:
                continue
            print(f"-- applying {m.id} ({m.path.name})")
            # In a real runner: open a transaction, execute m.text against the
            # target DB, commit. Here we just record success.
            record(m.id)
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
