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

# The listed historical versions were published with an LGPL-2.1 label for
# rasky/go-lzo despite shipping its actual GPLv2 license text. They have
# an additive, verified GPLv2 erratum in their Release description.
# Existing notice assets are immutable: accept ONLY a byte-for-byte verified
# legacy rendering that differs solely in this one known license label.
# All new versions must use the corrected classification and have no exemption.
LEGACY_GOLZO_VERSIONS = {f"v1.19.{v}" for v in range(26, 33)}
GOLZO = "github.com/rasky/go-lzo@v0.0.0-20200203143853-96a758eda86e"
ERRATA_MARKER = "<!-- mipsel-source-errata-20261011 -->"



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


def _approved_legacy_bytes(release, name, corrected):
    """Reverse ONLY the known go-lzo license label for already published assets.

    Actual SHA-256 + bytes remain verified by check_asset. No generic drift
    exemption; this is restricted to seven tags with reviewed Release errata.
    """
    tag = release.get("tag_name", "")
    version = tag.removeprefix("mipsel-")
    if version not in LEGACY_GOLZO_VERSIONS or tag != "mipsel-" + version:
        return None
    body = release.get("body")
    if not isinstance(body, str) or body.count(ERRATA_MARKER) != 1:
        return None
    summary_name = f"THIRD_PARTY_LICENSES-{version}.txt"
    entries = [x for x in release["assets"] if x["name"] == summary_name]
    if len(entries) != 1:
        return None
    digest = entries[0].get("digest")
    if (not isinstance(digest, str)
            or "Original summary digest: " + digest not in body
            or "GPL version 2" not in body
            or GOLZO not in body):
        return None
    expected = expected_names(tag)
    if name not in expected:
        return None
    text = corrected.decode("utf-8")
    module = re.escape(GOLZO)
    if name == expected[0]:
        # Only the original module-table row and its copyleft summary line.
        text, n1 = re.subn(
            r"^(" + module + r" \| )GPL-2\.0( \| LICENSE\.gpl \|)",
            r"\g<1>LGPL-2.1\2", text, flags=re.M)
        text, n2 = re.subn(
            r"^([ \t]+" + module + r" -> )GPL-2\.0([ \t]*)$",
            r"\g<1>LGPL-2.1\2", text, flags=re.M)
        if n1 != 1 or n2 != 1:
            return None
    else:
        text, n = re.subn(
            r"^(--- " + module + r" \| license: )GPL-2\.0( \| files: LICENSE\.gpl)$",
            r"\g<1>LGPL-2.1\2", text, flags=re.M)
        if n != 1:
            return None
    return text.encode("utf-8")


def verify_asset_with_audited_erratum(api, repo, release, name, corrected):
    """Verify current bytes, or a precisely reconstructed immutable legacy set."""
    try:
        return check_asset(api, repo, release, name, corrected)
    except assets.MetadataError:
        legacy = _approved_legacy_bytes(release, name, corrected)
        if legacy is None or legacy == corrected:
            raise
        result = check_asset(api, repo, release, name, legacy)
        if result is not None:
            print(f"Verified immutable legacy notice with pinned GPLv2 erratum: {name}")
        return result


def publish(api, repo, tag, files):
    """files: mapping of asset name -> local path. Returns names uploaded."""
    names = expected_names(tag)
    if tuple(files) != names:
        raise assets.MetadataError("Expected summary and full notices for the tag version")
    local = {name: load_local(path, name) for name, path in files.items()}
    release = assets.read_release(api, repo, tag)
    protected = {a["name"]: a for a in release["assets"]
                 if a["name"] not in names}
    # Preflight ALL existing notices before making even the first upload.
    # Otherwise a corrupt full-text asset could be discovered only after
    # the valid summary was already added, leaving a partial mutation.
    for name in names:
        verify_asset_with_audited_erratum(api, repo, release, name, local[name])
    uploaded = []
    for name in names:
        release = assets.read_release(api, repo, tag)
        current = verify_asset_with_audited_erratum(api, repo, release, name, local[name])
        if current is not None:
            continue
        # Re-read just before upload; reject unexpected release changes.
        fresh = assets.read_release(api, repo, tag)
        if fresh["id"] != release["id"]:
            raise assets.MetadataError(f"Release changed before notice upload {name}")
        if verify_asset_with_audited_erratum(api, repo, fresh, name, local[name]) is not None:
            continue  # appeared concurrently and matches: idempotent success
        now_protected = {a["name"]: a for a in fresh["assets"] if a["name"] not in names}
        if now_protected != protected:
            raise assets.MetadataError(f"Release assets changed before notice upload {name}")
        api.upload(tag, Path(files[name]))
        verified = assets.read_release(api, repo, tag)
        if verify_asset_with_audited_erratum(api, repo, verified, name, local[name]) is None:
            raise assets.MetadataError(f"Notice upload {name} was not verified; inspect release manually")
        if {a["name"]: a for a in verified["assets"] if a["name"] not in names} != protected:
            raise assets.MetadataError(f"Release assets changed after notice upload {name}")
        uploaded.append(name)
    return uploaded


def verify_existing(api, repo, tag, files):
    """Read-only: require both published notice assets to match their exact bytes."""
    names = expected_names(tag)
    if tuple(files) != names:
        raise assets.MetadataError("Expected summary and full notices for tag version")
    local = {name: load_local(path, name) for name, path in files.items()}
    release = assets.read_release(api, repo, tag)
    for name in names:
        if verify_asset_with_audited_erratum(
                api, repo, release, name, local[name]) is None:
            raise assets.MetadataError(f"Missing published notice: {name}")
    print("Both immutable release notices verified against rebuilt content")


def main():
    if len(sys.argv) != 5:
        raise assets.MetadataError("Expected: release_notices.py publish <tag> <summary> <full>")
    import os
    command, tag, summary, full = sys.argv[1:5]
    if command not in ("publish", "verify"):
        raise assets.MetadataError("Invalid command")
    repository = os.environ.get("GITHUB_REPOSITORY")
    if not repository:
        raise assets.MetadataError("GITHUB_REPOSITORY is not set; refusing to guess")
    files = {expected_names(tag)[0]: summary, expected_names(tag)[1]: full}
    if command == "verify":
        verify_existing(assets.GitHub(), repository, tag, files)
    else:
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
