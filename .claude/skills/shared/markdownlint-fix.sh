#!/usr/bin/env bash
# Auto-fix markdown lint issues on a single file.
# Used as a PostToolUse hook for Edit/Write on .md files.
# Exits 0 always (hook safety).

file_path="$1"

case "$file_path" in
  *.md)
    if command -v markdownlint-cli2 >/dev/null 2>&1; then
      markdownlint-cli2 --fix "$file_path" 2>/dev/null || true
    elif command -v markdownlint >/dev/null 2>&1; then
      markdownlint --fix "$file_path" 2>/dev/null || true
    fi
    ;;
esac
