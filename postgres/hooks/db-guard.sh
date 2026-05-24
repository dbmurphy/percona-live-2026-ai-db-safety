#!/usr/bin/env bash
# Postgres PreToolUse hook.
#
# Reads a JSON tool-call payload from stdin and decides whether to allow,
# block, or pass through. Emits one JSON object on stdout:
#   {"decision":"allow"}  or  {"decision":"block","reason":"..."}
#
# This is the floor under CLAUDE.md and skills: even if those fail, this
# refuses obviously destructive or unbounded statements.

set -euo pipefail

if ! command -v jq >/dev/null 2>&1; then
  echo '{"decision":"block","reason":"db-guard: jq is required but not installed"}'
  exit 0
fi

payload="$(cat)"
sql="$(printf '%s' "$payload" | jq -r '.tool_input.sql // .tool_input.query // ""')"

if [[ -z "$sql" ]]; then
  printf '{"decision":"allow"}\n'
  exit 0
fi

# Normalize: collapse whitespace, uppercase for keyword checks.
norm="$(printf '%s' "$sql" | tr '[:lower:]' '[:upper:]' | tr -s '[:space:]' ' ')"

block() {
  local reason="$1"
  jq -n --arg r "$reason" '{decision:"block", reason:$r}'
  exit 0
}

# 1. Hard-block destructive DDL/DML.
case "$norm" in
  *"DROP TABLE"*|*"DROP DATABASE"*|*"DROP SCHEMA"*|*"DROP INDEX"*)
    block "destructive DDL detected (DROP). Emit a migration with up+down instead." ;;
  *"TRUNCATE"*)
    block "TRUNCATE detected. Emit a migration for human review." ;;
  *"CREATE INDEX"*|*"REINDEX"*)
    block "index change detected. Emit a migration; never run DDL from the assistant." ;;
esac

# 2. Block unbounded UPDATE/DELETE.
if [[ "$norm" == *"UPDATE "* || "$norm" == *"DELETE "* ]]; then
  if [[ "$norm" != *" WHERE "* ]] || [[ "$norm" == *" WHERE TRUE"* ]] || [[ "$norm" == *" WHERE 1=1"* ]]; then
    block "unbounded UPDATE/DELETE detected. The MCP server should be read-only — this should never reach here."
  fi
  block "write statement detected. The assistant is read-only; emit a migration."
fi

# 3. Block writes smuggled in CTEs (WITH ... AS (INSERT ...) SELECT ...).
if [[ "$norm" == *"WITH "* ]] && \
   { [[ "$norm" == *"INSERT "* ]] || [[ "$norm" == *"UPDATE "* ]] || [[ "$norm" == *"DELETE "* ]]; }; then
  block "writable CTE detected. Read-only assistants do not emit data-modifying CTEs."
fi

printf '{"decision":"allow"}\n'
exit 0
