# SPDX-License-Identifier: MIT
"""Fail-closed pre/post snapshots for one historical MIPSel release.

No GitHub writes occur here: release modifications are made only by the
existing, individually tested release_assets/license/notices publishers.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

HISTORIC = tuple(f"1.19.{n}" for n in range(24, 32))


class BackfillError(Exception):
    pass


def valid_version(version):
    if version not in HISTORIC:
        raise BackfillError("Only explicitly enumerated historical versions are allowed")
    return version


def asset_names(version):
    version = valid_version(version)
    binary = f"mihomo-linux-mipsel-softfloat-v{version}"
    return (binary, binary + ".sha256", binary + ".LICENSE",
            f"THIRD_PARTY_LICENSES-v{version}.txt",
            f"THIRD_PARTY_NOTICES-v{version}.txt")


def manifest(payload, version):
    expected_tag = "mipsel-v" + valid_version(version)
    if (not isinstance(payload, dict) or payload.get("tag_name") != expected_tag
            or payload.get("draft") is not False
            or not isinstance(payload.get("assets"), list)
            or type(payload.get("id")) is not int or payload["id"] <= 0):
        raise BackfillError("Release tag/id/draft/asset-list mismatch")
    found, identities = {}, set()
    for asset in payload["assets"]:
        if not isinstance(asset, dict):
            raise BackfillError("Malformed release asset")
        name, ident = asset.get("name"), asset.get("id")
        digest = asset.get("digest")
        if (not isinstance(name, str) or not name or name in found
                or type(ident) is not int or ident <= 0 or ident in identities
                or type(asset.get("size")) is not int or asset["size"] < 0
                or not isinstance(digest, str) or not re.fullmatch(r"sha256:[a-f0-9]{64}", digest)
                or asset.get("state") != "uploaded"):
            raise BackfillError("Duplicate, incomplete or malformed release asset")
        found[name] = {k: asset[k] for k in ("id", "size", "digest", "state")}
        identities.add(ident)
    binary = asset_names(version)[0]
    if binary not in found or found[binary]["size"] == 0:
        raise BackfillError("Missing historical published binary")
    return {"release_id": payload["id"], "tag": expected_tag, "assets": found}


def check_binary_bytes(manifest_data, version, data):
    binary = asset_names(version)[0]
    found = manifest_data["assets"][binary]
    if len(data) != found["size"] or "sha256:" + hashlib.sha256(data).hexdigest() != found["digest"]:
        raise BackfillError("Downloaded binary differs from immutable GitHub digest/size")


def compare_snapshots(before, after, version):
    """All preexisting assets must preserve identity; only 4 intended additions."""
    if before["release_id"] != after["release_id"] or before["tag"] != after["tag"]:
        raise BackfillError("Release identity changed")
    allowed = set(asset_names(version)[1:])
    old, new = before["assets"], after["assets"]
    if any(name not in new or new[name] != meta for name, meta in old.items()):
        raise BackfillError("Existing release assets changed or disappeared")
    if set(new) - set(old) - allowed:
        raise BackfillError("Unexpected asset appeared during publication")
    if not set(asset_names(version)).issubset(new):
        raise BackfillError("License/checksum/notice assets are missing after publish")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("before", "after"))
    parser.add_argument("--version", required=True)
    parser.add_argument("--release-json", required=True)
    parser.add_argument("--binary", required=True)
    parser.add_argument("--snapshot", default="historic-before.json")
    args = parser.parse_args()
    version = valid_version(args.version)
    release = manifest(json.loads(Path(args.release_json).read_text()), version)
    check_binary_bytes(release, version, Path(args.binary).read_bytes())

    if args.stage == "before":
        if Path(args.snapshot).exists():
            raise BackfillError("Refusing to overwrite a prior before-snapshot")
        Path(args.snapshot).write_text(json.dumps(release, indent=2) + "\n")
        print(f"PREPARED {release['tag']} release_id={release['release_id']} "
              f"existing_assets={len(release['assets'])}")
    else:
        previous = json.loads(Path(args.snapshot).read_text())
        compare_snapshots(previous, release, version)
        print(f"VERIFIED {release['tag']} release_id={release['release_id']} "
              "existing assets unchanged, expected notices present")


if __name__ == "__main__":
    try:
        main()
    except (BackfillError, OSError, ValueError, KeyError) as error:
        print(f"Historical backfill verification refused: {error}", file=sys.stderr)
        sys.exit(2)
