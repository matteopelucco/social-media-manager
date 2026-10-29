#!/usr/bin/env bash
# Creates or updates the ruleset of the default branch from .github/rulesets/main.json: PR required,
# gate `verifica` required, no force push, no deletion, no bypass. Idempotent.
# For a human with admin rights: the agents' guard hooks deny `gh api ... /rulesets` on purpose.
set -euo pipefail

file="$(cd "$(dirname "$0")/.." && pwd)/.github/rulesets/main.json"
repo="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"
name="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["name"])' "$file")"

id="$(gh api "repos/$repo/rulesets" --jq ".[] | select(.name==\"$name\") | .id" | head -n1)"
if [ -n "$id" ]; then
  gh api -X PUT "repos/$repo/rulesets/$id" --input "$file" >/dev/null
  echo "Ruleset '$name' aggiornato ($repo)."
else
  gh api -X POST "repos/$repo/rulesets" --input "$file" >/dev/null
  echo "Ruleset '$name' creato ($repo)."
fi
