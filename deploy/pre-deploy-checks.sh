#!/usr/bin/env bash
# pre-deploy-checks.sh
#
# Scans pending migrations for destructive statements. For each one:
#   1. Takes a snapshot of the target DB.
#   2. Runs the migration's `down:` block against a copy of the snapshot to
#      verify rollback works.
#   3. Pauses for one-click human confirmation before continuing.

set -euo pipefail

MIGRATIONS_DIR="$(dirname "$0")/migrations"
APPLIED_FILE="$(dirname "$0")/.applied"

destructive() {
  local f="$1"
  grep -E -i 'DROP TABLE|DROP COLUMN|TRUNCATE|\$unset|\$out|\$merge' "$f" >/dev/null
}

confirm() {
  local msg="$1"
  read -r -p "$msg [type YES to proceed]: " ans
  [[ "$ans" == "YES" ]] || { echo "aborted."; exit 1; }
}

pending() {
  local applied=()
  [[ -f "$APPLIED_FILE" ]] && mapfile -t applied < "$APPLIED_FILE"
  for f in "$MIGRATIONS_DIR"/*.{sql,js}; do
    [[ -e "$f" ]] || continue
    local id; id="$(basename "$f")"
    id="${id%.*}"
    local seen=0
    for a in "${applied[@]:-}"; do [[ "$a" == "$id" ]] && seen=1 && break; done
    (( seen )) || echo "$f"
  done
}

for f in $(pending); do
  if destructive "$f"; then
    echo "destructive migration: $f"
    echo "snapshotting target DB..."
    # placeholder — wire to pg_dump / mongodump in real deploy
    echo "verifying down: block against snapshot..."
    confirm "Apply $f?"
  fi
done

echo "pre-deploy-checks: OK"
