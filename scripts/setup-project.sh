#!/usr/bin/env bash
# Creates the GitHub Project that orders the backlog (top = highest priority), if it does not exist,
# and links it to the repository. Idempotent. Requires `gh` authenticated with the `project` scope:
#   gh auth refresh -s project
# The default Status field (Todo / In Progress / Done) is enough; add "Need Info" by hand in the UI.
set -euo pipefail

owner="${1:-$(gh repo view --json owner --jq .owner.login)}"
repo="$(gh repo view --json name --jq .name)"
title="${2:-$repo}"

number="$(gh project list --owner "$owner" --format json --jq ".projects[] | select(.title==\"$title\") | .number" | head -n1)"
if [ -z "$number" ]; then
  number="$(gh project create --owner "$owner" --title "$title" --format json --jq .number)"
  echo "Project creato: #$number"
else
  echo "Project già presente: #$number"
fi
gh project link "$number" --owner "$owner" --repo "$owner/$repo" >/dev/null 2>&1 || true
echo "Fatto: https://github.com/$owner/$repo/projects"
