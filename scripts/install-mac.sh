#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_skills="$repo_root/skills"
codex_skills="$HOME/.codex/skills"

mkdir -p "$repo_skills" "$codex_skills"

find "$repo_skills" -mindepth 1 -maxdepth 1 -type d | while read -r skill_dir; do
  name="$(basename "$skill_dir")"
  link="$codex_skills/$name"

  if [ -e "$link" ] || [ -L "$link" ]; then
    echo "skip: $link already exists"
    continue
  fi

  ln -s "$skill_dir" "$link"
  echo "linked: $link -> $skill_dir"
done
