#!/usr/bin/env bash
# Discover the project's verification/CI command.
#
# Searches for common project configuration files and returns the
# appropriate test/check command. Exits 1 if no verification command found.
#
# Usage: discover-verification-cmd.sh [directory]
# Output: Prints the verification command to stdout

set -euo pipefail

dir="${1:-.}"
cd "$dir"

if [ -f justfile ] && grep -qE '^(check|ci):' justfile; then
  recipe=$(grep -oE '^(ci|check):' justfile | head -1 | tr -d ':')
  echo "just $recipe"
elif [ -f Makefile ] && grep -qE '^(ci|check|test):' Makefile; then
  target=$(grep -oE '^(ci|check|test):' Makefile | head -1 | tr -d ':')
  echo "make $target"
elif [ -f pyproject.toml ] && grep -q '\[tool\.poe\.tasks' pyproject.toml; then
  # Python project with poe — check before package.json so monorepos that
  # carry a TS workspace at the root still resolve to the documented Python
  # gate (`uv run poe check`). `poe` is rarely on PATH outside `uv run`.
  if grep -qE '^check\s*=' pyproject.toml; then
    echo "uv run poe check"
  else
    echo "uv run poe test"
  fi
elif [ -f package.json ] && command -v jq >/dev/null; then
  if jq -e '.scripts.check' package.json >/dev/null 2>&1; then
    echo "npm run check"
  elif jq -e '.scripts.test' package.json >/dev/null 2>&1; then
    echo "npm test"
  else
    echo "No verification command found in package.json" >&2
    exit 1
  fi
elif [ -f Cargo.toml ]; then
  echo "cargo test"
elif [ -f flake.nix ]; then
  echo "nix flake check"
elif [ -f pyproject.toml ]; then
  echo "pytest"
else
  echo "No verification command found" >&2
  exit 1
fi
