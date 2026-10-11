# SPDX-License-Identifier: MIT
"""Recover compiler versions from published historic MIPSel binaries.

Always verifies SHA-256 against GitHub Release asset API metadata before
reading Go build info. Does not modify Release descriptions or assets.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

REPO = "saymer-alt/mihomo-auto-build"


def run(*args):
    p = subprocess.run(args, capture_output=True, text=True, check=False)
    if p.returncode:
        raise RuntimeError(f"{' '.join(args[:3])}: {p.stderr[:350]}")
    return p.stdout


def digest_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1024 * 1024), b""):
            h.update(part)
    return "sha256:" + h.hexdigest()


def parse_build_info(output, version):
    match = re.search(r"^.+:\s+(go\d+\.\d+(?:\.\d+)?)$", output, re.M)
    if not match:
        raise ValueError(f"Missing Go toolchain build info for {version}")
    module = re.search(r"^\s*mod\s+github.com/metacubex/mihomo\s+(\S+)", output, re.M)
    if not module or module.group(1) != version:
        raise ValueError("Unexpected upstream module version in archived binary")
    return {"go_version": match.group(1), "main_module_version": module.group(1)}


def audit(first=24, last=28):
    results = []
    with tempfile.TemporaryDirectory(prefix="mipsel-archive-audit-") as work:
        directory = Path(work)
        for minor in range(first, last + 1):
            version = f"v1.19.{minor}"
            tag = "mipsel-" + version
            name = "mihomo-linux-mipsel-softfloat-" + version
            release = json.loads(run("gh", "api", f"repos/{REPO}/releases/tags/{tag}"))
            if release.get("tag_name") != tag:
                raise ValueError("Release tag mismatch")
            binaries = [a for a in release.get("assets", []) if a.get("name") == name]
            if len(binaries) != 1:
                raise ValueError("Expected one archived binary: " + name)
            asset = binaries[0]
            expected = asset.get("digest")
            if not isinstance(expected, str) or not re.fullmatch(r"sha256:[a-f0-9]{64}", expected):
                raise ValueError("Missing canonical SHA-256")
            local = directory / name
            run("gh", "release", "download", tag, "-R", REPO, "-p", name, "-O", str(local))
            if local.stat().st_size != asset["size"] or digest_file(local) != expected:
                raise ValueError("Release original binary digest mismatch: " + version)
            info = parse_build_info(run("go", "version", "-m", str(local)), version)
            results.append({"tag": tag, "asset_id": asset["id"], "asset_sha256": expected,
                            **info, "verification": "GitHub API digest and Go build-info"})
            print(f"{tag}: {info['go_version']}  SHA-256 VERIFIED", flush=True)
            local.unlink()
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    items = audit()
    args.output.write_text(json.dumps(items, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
