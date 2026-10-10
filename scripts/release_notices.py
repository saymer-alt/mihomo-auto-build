# SPDX-License-Identifier: MIT
"""Verify and attach third-party notice assets to a release, never clobbering.

Expected assets for tag `mipsel-vX.Y.Z`:
  THIRD_PARTY_LICENSES-vX.Y.Z.txt  (compact summary)
  THIRD_PARTY_NOTICES-vX.Y.Z.txt   (full license texts)

For each expected asset:
  * exactly one same-named asset may exist; duplicates refuse;
  * an existing asset must be `uploaded`, must match the local file byte for
    byte and in GitHub's recorded sha256 digest and size - otherwise the run
    fails closed instead of trusting the name;
  * a missing asset is uploaded (no --clobber) and verified afterwards;
  * binaries, checksums and unrelated assets are never touched, and nothing
    is ever deleted here.
"""
import hashlib
from pathlib import Path
import re
import subprocess
import sys

import release_assets as assets

NOTICE_MAX_BYTES = 8 * 1024 * 1024


def expected_names(tag):
    if not re.fullmatch(r"mipsel-v[0-9]+\.[0-9]+\.[0-9]+", tag):
        raise assets.MetadataError("Invalid release tag")
    version = tag.removeprefix("mipsel-")
    return (f"THIRD_PARTY_LICENSES-{version}.txt",
            f"THIRD_PARTY_NOTICES-{version}.txt")


def load_local(path, name):
    local = Path(path)
    if not local.is_file() or local.stat().st_size == 0:
        raise assets.MetadataError(f"Local notice file missing or empty: {path}")
    content = local.read_bytes()
    if len(content) > NOTICE_MAX_BYTES:
        raise assets.MetadataError(f"Notice file exceeds {NOTICE_MAX_BYTES} bytes: {name}")
    if b"\x00" in content[:4096]:
        raise assets.MetadataError(f"Notice file looks binary: {name}")
    try:
        content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise assets.MetadataError(f"Notice file is not valid UTF-8: {name}") from exc
    return content


def check_asset(api, repo, release, name, content):
    matches = [a for a in release["assets"] if a["name"] == name]
    if len(matches) > 1:
        raise assets.MetadataError(f"Duplicate notice assets named {name}")
    if not matches:
        return None
    asset = matches[0]
    if (type(asset.get("id")) is not int or asset["id"] <= 0
            or asset.get("state") != "uploaded"
            or sum(a.get("id") == asset["id"] for a in release["assets"]) != 1):
        raise assets.MetadataError(f"Invalid/partial notice asset {name}: manual review required")
    if asset["size"] != len(content) or assets.digest(asset) != hashlib.sha256(content).hexdigest():
        raise assets.MetadataError(f"Existing notice asset {name} does not match generated content")
    raw = api.api(f'repos/{repo}/releases/assets/{asset["id"]}', raw=True)
    if raw != content:
        raise assets.MetadataError(f"Existing notice asset {name} bytes differ from generated content")
    return asset


def publish(api, repo, tag, files):
    """files: mapping of asset name -> local path. Returns names uploaded."""
    names = expected_names(tag)
    if tuple(files) != names:
        raise assets.MetadataError("Expected summary and full notices for the tag version")
    local = {name: load_local(path, name) for name, path in files.items()}
    release = assets.read_release(api, repo, tag)
    protected = {a["name"]: a for a in release["assets"]
                 if a["name"] not in names}
    uploaded = []
    for name in names:
        release = assets.read_release(api, repo, tag)
        current = check_asset(api, repo, release, name, local[name])
        if current is not None:
            continue
        # Re-read just before upload; reject unexpected release changes.
        fresh = assets.read_release(api, repo, tag)
        if fresh["id"] != release["id"]:
            raise assets.MetadataError(f"Release changed before notice upload {name}")
        if check_asset(api, repo, fresh, name, local[name]) is not None:
            continue  # appeared concurrently and matches: idempotent success
        now_protected = {a["name"]: a for a in fresh["assets"] if a["name"] not in names}
        if now_protected != protected:
            raise assets.MetadataError(f"Release assets changed before notice upload {name}")
        api.upload(tag, Path(files[name]))
        verified = assets.read_release(api, repo, tag)
        if check_asset(api, repo, verified, name, local[name]) is None:
            raise assets.MetadataError(f"Notice upload {name} was not verified; inspect release manually")
        if {a["name"]: a for a in verified["assets"] if a["name"] not in names} != protected:
            raise assets.MetadataError(f"Release assets changed after notice upload {name}")
        uploaded.append(name)
    return uploaded


def main():
    if len(sys.argv) != 5:
        raise assets.MetadataError("Expected: release_notices.py publish <tag> <summary> <full>")
    import os
    command, tag, summary, full = sys.argv[1:5]
    if command != "publish":
        raise assets.MetadataError("Invalid command")
    repository = os.environ.get("GITHUB_REPOSITORY")
    if not repository:
        raise assets.MetadataError("GITHUB_REPOSITORY is not set; refusing to guess")
    files = {expected_names(tag)[0]: summary, expected_names(tag)[1]: full}
    uploaded = publish(assets.GitHub(), repository, tag, files)
    print("Third-party notices verified" +
          (" and uploaded: " + ", ".join(uploaded) if uploaded else "; already present"))


if __name__ == "__main__":
    try:
        main()
    except (assets.MetadataError, assets.NotFound, subprocess.CalledProcessError,
            OSError, ValueError) as e:
        print(f"Notice publication refused: {e}", file=sys.stderr)
        sys.exit(2)
