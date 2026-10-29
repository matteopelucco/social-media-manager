#!/usr/bin/env bash
# Prints "docs" when every file changed since <base> is documentation, "code" otherwise.
# Usage: scripts/classify-changes.sh <base-ref>   (default origin/main)
set -euo pipefail

base="${1:-origin/main}"
files="$(git diff --name-only "$base"...HEAD)"
[ -n "$files" ] || { echo docs; exit 0; }

while IFS= read -r f; do
  case "$f" in
    docs/*|*.md|LICENSE|.github/ISSUE_TEMPLATE/*|.github/pull_request_template.md) ;;
    *) echo code; exit 0 ;;
  esac
done <<< "$files"
echo docs
