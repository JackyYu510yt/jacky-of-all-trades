#!/usr/bin/env bash
# install.sh — Unix/macOS/Git-Bash installer for jacky-of-all-trades skills
#
# Creates symlinks from ~/.claude/skills/<name> to each skill folder in this repo,
# so edits / git pulls here propagate automatically to Claude Code.
#
# Usage:
#   cd <path-to-cloned-repo>
#   bash install.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$HOME/.claude/skills"

mkdir -p "$SKILLS_DIR"

shopt -s nullglob
skills=()
for dir in "$REPO_ROOT"/*/; do
  name="$(basename "$dir")"
  [ -f "$dir/SKILL.md" ] && skills+=("$name")
done

if [ ${#skills[@]} -eq 0 ]; then
  echo "error: no skill folders (containing SKILL.md) found in $REPO_ROOT" >&2
  exit 1
fi

echo "found ${#skills[@]} skill(s): ${skills[*]}"
echo

for name in "${skills[@]}"; do
  src="$REPO_ROOT/$name"
  dst="$SKILLS_DIR/$name"

  if [ -L "$dst" ]; then
    rm "$dst"
    echo "  [replaced] $name"
  elif [ -e "$dst" ]; then
    echo "  [skipped]  $name — real folder already exists at $dst. Delete or rename it, then rerun." >&2
    continue
  else
    echo "  [added]    $name"
  fi

  ln -s "$src" "$dst"
done

echo
echo "done. Claude Code will discover skills at $SKILLS_DIR on next session."
echo "to update later: cd $REPO_ROOT && git pull   (no reinstall needed)"
