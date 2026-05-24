#!/usr/bin/env bash
# MongoDB PreToolUse hook.
#
# Reads a JSON tool-call payload from stdin and decides allow/block.
# Output: {"decision":"allow"} or {"decision":"block","reason":"..."}
#
# Blocks:
#   1. createIndex / dropIndex tool calls.
#   2. $out, $merge, $function anywhere in a pipeline (including nested
#      $lookup.pipeline stages).
#   3. Aggregations on hot collections that do not start with $match.

set -euo pipefail

if ! command -v jq >/dev/null 2>&1; then
  echo '{"decision":"block","reason":"db-guard: jq is required but not installed"}'
  exit 0
fi

payload="$(cat)"
tool="$(printf '%s' "$payload" | jq -r '.tool_name // ""')"
coll="$(printf '%s' "$payload" | jq -r '.tool_input.collection // ""')"
pipeline="$(printf '%s' "$payload" | jq -c '.tool_input.pipeline // []')"

block() {
  jq -n --arg r "$1" '{decision:"block", reason:$r}'
  exit 0
}

# 1. Block index DDL by tool name.
case "$tool" in
  *createIndex*|*dropIndex*|*createCollection*|*dropCollection*|*dropDatabase*|*renameCollection*)
    block "DDL tool call ($tool) detected. Emit a migration with up+down." ;;
esac

# 2. Recursive scan for forbidden stages anywhere in the pipeline tree.
# jq walks every value; we flag any object key matching $out/$merge/$function.
forbidden="$(printf '%s' "$pipeline" | jq -r '
  [ .. | objects | keys[] ]
  | map(select(. == "$out" or . == "$merge" or . == "$function"))
  | unique
  | join(",")
')"
if [[ -n "$forbidden" ]]; then
  block "forbidden stage(s) in pipeline: $forbidden — these are writes or arbitrary code execution."
fi

# 3. Aggregations on hot collections must start with $match.
case "$coll" in
  activity|users|sessions)
    first_stage="$(printf '%s' "$pipeline" | jq -r '.[0] | keys[0] // ""')"
    if [[ -n "$first_stage" && "$first_stage" != "\$match" ]]; then
      block "pipeline on hot collection '$coll' must start with \$match; first stage was '$first_stage'."
    fi
    ;;
esac

printf '{"decision":"allow"}\n'
exit 0
