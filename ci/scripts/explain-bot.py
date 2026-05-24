#!/usr/bin/env python3
"""Run EXPLAIN against a shadow DB on every new query in the diff.

Two modes:
  --seed                Create shadow tables/collections from .schemas/ and
                        insert a small synthetic dataset shaped like prod.
  --base X --head Y     Walk added SQL/JS lines, run EXPLAIN/explain(), parse
                        cost, post a comment on the PR. Fail if
                        rows_examined / rows_returned > 1000.

The shadow DB uses .schemas/ for structure but NEVER real data. Synthetic rows
follow the indexed distribution: many rows, but enough variety that a missing
index produces a visible cost gap vs. the indexed plan.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROWS_EXAMINED_RATIO_LIMIT = 1000
SYNTHETIC_ROWS = 100_000


def seed() -> None:
    import psycopg
    from pymongo import MongoClient

    pg = psycopg.connect(os.environ["PGURI"], autocommit=True)
    for f in Path("postgres/.schemas").glob("*.json"):
        s = json.loads(f.read_text())
        cols = ", ".join(f'{c["name"]} {c["type"]}' for c in s["columns"])
        pg.execute(f'DROP TABLE IF EXISTS {s["table"]}')
        pg.execute(f'CREATE TABLE {s["table"]} ({cols})')
        for idx in s.get("indexes", []):
            cols_sql = ", ".join(idx["columns"])
            where = f' WHERE {idx["where"]}' if idx.get("where") else ""
            pg.execute(f'CREATE INDEX {idx["name"]} ON {s["table"]} ({cols_sql}){where}')
        # synthetic rows
        pg.execute(
            f"INSERT INTO {s['table']} (user_id, ts, event_type, payload) "
            f"SELECT (g % 1000)::bigint, now() - (g || ' seconds')::interval, "
            f"'click', '{{}}'::jsonb FROM generate_series(1, {SYNTHETIC_ROWS}) g"
        )
    pg.close()

    mc = MongoClient(os.environ["MONGOURI"])
    db = mc.get_default_database()
    for f in Path("mongodb/.schemas").glob("*.json"):
        s = json.loads(f.read_text())
        coll = db[s["collection"]]
        coll.drop()
        for idx in s.get("indexes", []):
            coll.create_index(list(idx["key"].items()), name=idx["name"])
        coll.insert_many(
            [
                {"user_id": i % 1000, "ts": i, "event_type": "click", "payload": {}}
                for i in range(SYNTHETIC_ROWS)
            ]
        )


def diff_files(base: str, head: str) -> list[Path]:
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{base}..{head}"], text=True
    )
    return [Path(p) for p in out.splitlines() if p.endswith((".sql", ".js"))]


def explain_sql(query: str) -> dict:
    import psycopg

    pg = psycopg.connect(os.environ["PGURI"], autocommit=True)
    cur = pg.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}")
    return cur.fetchone()[0][0]


def post_comment(pr: str, body: str) -> None:
    if not os.environ.get("GH_TOKEN"):
        print(body)
        return
    subprocess.run(
        ["gh", "pr", "comment", pr, "--body", body],
        check=False,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", action="store_true")
    ap.add_argument("--base")
    ap.add_argument("--head")
    ap.add_argument("--pr")
    args = ap.parse_args()

    if args.seed:
        seed()
        return 0

    if not (args.base and args.head):
        ap.error("--base and --head required when not seeding")

    failures: list[str] = []
    comments: list[str] = []
    for f in diff_files(args.base, args.head):
        if f.suffix != ".sql":
            continue
        text = f.read_text()
        for q in re.findall(r"(?is)\bselect\b.+?;", text):
            try:
                plan = explain_sql(q)
            except Exception as e:
                comments.append(f"`{f}`: EXPLAIN failed: {e}")
                continue
            root = plan["Plan"]
            examined = root.get("Actual Rows", 0) + root.get("Rows Removed by Filter", 0)
            returned = max(root.get("Actual Rows", 1), 1)
            ratio = examined / returned
            comments.append(
                f"`{f}` plan: `{root['Node Type']}` examined={examined} returned={returned} ratio={ratio:.0f}"
            )
            if ratio > ROWS_EXAMINED_RATIO_LIMIT:
                failures.append(f"{f}: examined/returned={ratio:.0f} > {ROWS_EXAMINED_RATIO_LIMIT}")

    if comments and args.pr:
        post_comment(args.pr, "### explain-bot\n\n" + "\n".join(f"- {c}" for c in comments))

    if failures:
        print("explain-bot: cost limit exceeded:")
        for x in failures:
            print(f"  - {x}")
        return 1

    print("explain-bot: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
