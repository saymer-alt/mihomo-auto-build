# SPDX-License-Identifier: MIT
"""Attach the exact tagged upstream Mihomo MIT license without changing binaries.

Runs after the existing fail-closed release_assets.py publish step. A healthy
binary + checksum must already exist; only a missing LICENSE sidecar is added.
"""
import hashlib
from pathlib import Path
import re
import sys
import tempfile
from urllib.request import urlopen

import release_assets as assets


def license_name(binary):
    return binary + ".LICENSE"


def validate_license(content):
    if not isinstance(content, bytes) or not 200 <= len(content) <= 32768:
        raise assets.MetadataError("Invalid upstream LICENSE length")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as e:
        raise assets.MetadataError("Upstream LICENSE must be UTF-8") from e
    for phrase in ("Copyright 2023 KT", "Permission is hereby granted",
                   "THE SOFTWARE IS PROVIDED"):
        if phrase not in text:
            raise assets.MetadataError("Unexpected upstream LICENSE: human review required")
    return content


def download_tagged_license(tag):
    if not re.fullmatch(r"mipsel-v[0-9]+\.[0-9]+\.[0-9]+", tag):
        raise assets.MetadataError("Invalid release tag")
    upstream = tag.removeprefix("mipsel-")
    url = f"https://raw.githubusercontent.com/MetaCubeX/mihomo/{upstream}/LICENSE"
    try:
        with urlopen(url, timeout=30) as response:
            content = response.read(32769)
    except Exception as e:
        raise assets.MetadataError("Unable to read tagged upstream LICENSE") from e
    return validate_license(content)


def checked_notice(api, repo, tag, binary, content):
    """Validate existing notice object, if present, without any mutation."""
    release = assets.read_release(api, repo, tag)
    name = license_name(binary)
    matches = [a for a in release["assets"] if a["name"] == name]
    if len(matches) > 1:
        raise assets.MetadataError("Duplicate upstream LICENSE assets")
    if not matches:
        return None, release
    asset = matches[0]
    if (type(asset.get("id")) is not int or asset["id"] <= 0
            or type(asset.get("size")) is not int or asset["size"] <= 0
            or asset.get("state") != "uploaded"
            or sum(a.get("id") == asset["id"] for a in release["assets"]) != 1):
        raise assets.MetadataError("Invalid/partial LICENSE asset: no automatic deletion")
    if asset["size"] != len(content) or assets.digest(asset) != hashlib.sha256(content).hexdigest():
        raise assets.MetadataError("Existing LICENSE metadata does not match tagged upstream")
    raw = api.api(f'repos/{repo}/releases/assets/{asset["id"]}', raw=True)
    if raw != content:
        raise assets.MetadataError("Existing LICENSE bytes do not match tagged upstream")
    return asset, release


def ensure_license(api, repo, tag, binary, content):
    """Idempotent; never delete or replace any release asset."""
    content = validate_license(content)
    if not re.fullmatch(r"mipsel-v[0-9]+\.[0-9]+\.[0-9]+", tag):
        raise assets.MetadataError("Invalid release tag")
    if binary != "mihomo-linux-mipsel-softfloat-" + tag[7:]:
        raise assets.MetadataError("Invalid binary/tag pairing")
    before = assets.inspect(api, repo, tag, binary)
    if before["mode"] != "complete":
        raise assets.MetadataError("Binary and SHA-256 must be complete before LICENSE upload")
    current, release = checked_notice(api, repo, tag, binary, content)
    if current:
        return False

    # Re-read target assets just before uploading; reject unexpected changes.
    if assets.inspect(api, repo, tag, binary) != before:
        raise assets.MetadataError("Binary or checksum changed before LICENSE upload")
    again, fresh = checked_notice(api, repo, tag, binary, content)
    if again or fresh["id"] != release["id"]:
        raise assets.MetadataError("Release changed before LICENSE upload")
    target_names = {binary, binary + ".sha256"}
    targets = lambda rel: {a["name"]: a for a in rel["assets"] if a["name"] in target_names}
    if targets(fresh) != targets(release):
        raise assets.MetadataError("Release assets changed before LICENSE upload")

    # No --clobber. An unexpected concurrent notice must result in conflict.
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / license_name(binary)
        path.write_bytes(content)
        api.upload(tag, path)
    item, done = checked_notice(api, repo, tag, binary, content)
    if not item or done["id"] != release["id"] or targets(done) != targets(release):
        raise assets.MetadataError("LICENSE upload was not verified; inspect release manually")
    if assets.inspect(api, repo, tag, binary) != before:
        raise assets.MetadataError("Binary/checksum changed after LICENSE upload")
    return True


def main():
    if len(sys.argv) != 3:
        raise assets.MetadataError("Expected release tag and binary name")
    import os
    tag, binary = sys.argv[1:]
    content = download_tagged_license(tag)
    changed = ensure_license(assets.GitHub(), os.environ["GITHUB_REPOSITORY"],
                             tag, binary, content)
    print("Upstream MIT LICENSE verified" + (" and uploaded" if changed else "; already present"))


if __name__ == "__main__":
    try:
        main()
    except (assets.MetadataError, assets.NotFound, OSError, ValueError) as e:
        print(f"Release license check failed: {e}", file=sys.stderr)
        sys.exit(2)
