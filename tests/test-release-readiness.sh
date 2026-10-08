#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
tag=mipsel-v1.19.32
binary=mihomo-linux-mipsel-softfloat-v1.19.32
fixture=$tmpdir/release.json

jq -n --arg tag "$tag" --arg binary "$binary" '
  {tag_name: $tag, draft: false,
   assets: [
     {name: $binary, size: 52035739, digest: ("sha256:" + ("a" * 64))},
     {name: ($binary + ".sha256"), size: 114, digest: ("sha256:" + ("b" * 64))}
   ]}
' > "$fixture"
cp "$fixture" "$tmpdir/baseline.json"

expect_ready() {
  bash scripts/check-release-assets.sh "$fixture" "$tag" "$binary" >/dev/null
  echo "PASS: $1"
}
expect_repair() {
  if bash scripts/check-release-assets.sh "$fixture" "$tag" "$binary" >/dev/null 2>&1; then
    echo "FAIL: $1 incorrectly skipped rebuild" >&2
    exit 1
  fi
  echo "PASS: $1"
}
reset() { cp "$tmpdir/baseline.json" "$fixture"; }

expect_ready "complete release"
reset; jq '.assets = []' "$fixture" > "$tmpdir/out"; mv "$tmpdir/out" "$fixture"; expect_repair "empty assets"
reset; jq '.assets[0].name = "other-binary"' "$fixture" > "$tmpdir/out"; mv "$tmpdir/out" "$fixture"; expect_repair "wrong binary name"
reset; jq '.assets[0].size = 0' "$fixture" > "$tmpdir/out"; mv "$tmpdir/out" "$fixture"; expect_repair "zero-byte binary"
reset; jq '.assets += [.assets[0]]' "$fixture" > "$tmpdir/out"; mv "$tmpdir/out" "$fixture"; expect_repair "duplicate binary"
reset; jq '.assets = [.assets[0]]' "$fixture" > "$tmpdir/out"; mv "$tmpdir/out" "$fixture"; expect_repair "missing checksum"
reset; jq '.assets[0].digest = null' "$fixture" > "$tmpdir/out"; mv "$tmpdir/out" "$fixture"; expect_repair "missing digest"
reset; jq '.tag_name = "mipsel-v0.0.0"' "$fixture" > "$tmpdir/out"; mv "$tmpdir/out" "$fixture"; expect_repair "wrong tag"
echo "PASS: release readiness regression suite"
