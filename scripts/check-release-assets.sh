#!/usr/bin/env bash
# Exit 0: ready; 1: incomplete assets; 2: invalid API metadata.
set -euo pipefail

if [ "$#" -ne 3 ]; then
  echo "Usage: $0 RELEASE_JSON TAG EXPECTED_BINARY" >&2
  exit 2
fi

release_json=$1
expected_tag=$2
binary=$3
checksum="${binary}.sha256"

if ! jq -e 'type == "object" and (.assets | type == "array")' "$release_json" >/dev/null; then
  echo "Invalid release metadata" >&2
  exit 2
fi

if jq -e --arg tag "$expected_tag" --arg binary "$binary" --arg checksum "$checksum" '
  def asset_ok($name):
    [.assets[] | select(.name == $name)] as $matches |
    ($matches | length) == 1 and
    (($matches[0].size | type) == "number") and
    ($matches[0].size > 0) and
    (($matches[0].digest // "") | test("^sha256:[0-9a-f]{64}$"));

  .tag_name == $tag and
  .draft == false and
  asset_ok($binary) and
  asset_ok($checksum)
' "$release_json" >/dev/null; then
  echo "Release $expected_tag contains complete binary and checksum assets"
  exit 0
fi

echo "Release $expected_tag needs asset repair" >&2
exit 1
