#!/usr/bin/env bash
set -euo pipefail

PROFILE="$1"
MATRIX_FILE="${MATRIX_FILE:-.github/config/build-matrix.json}"

jq -e --arg p "$PROFILE" '.profiles[$p] // error("Unknown profile: \($p)")' \
  "$MATRIX_FILE" > /dev/null

python_versions=$(jq -c --arg p "$PROFILE" '.profiles[$p].python_versions' "$MATRIX_FILE")
echo "python_versions=$python_versions" >> "$GITHUB_OUTPUT"

operating_systems=$(jq -c --arg p "$PROFILE" '.profiles[$p].operating_systems' "$MATRIX_FILE")
if [ "$operating_systems" != "null" ]; then
  echo "operating_systems=$operating_systems" >> "$GITHUB_OUTPUT"
fi