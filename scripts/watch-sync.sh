#!/usr/bin/env bash
set -euo pipefail

interval="${1:-300}"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

while true; do
  "$script_dir/sync.sh" "sync: automatic workspace update" || true
  sleep "$interval"
done
