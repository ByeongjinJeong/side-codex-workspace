#!/usr/bin/env bash
set -euo pipefail

message="${1:-sync: update workspace}"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

git pull --rebase --autostash
git add .

if [ -z "$(git status --porcelain)" ]; then
  echo "nothing to commit"
  exit 0
fi

git commit -m "$message"
git push
