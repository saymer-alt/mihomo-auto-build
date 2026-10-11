# SPDX-License-Identifier: MIT
"""Safe additive source pointers and GPLv2 erratum in historical Release bodies.

Only PATCHes Release descriptions, never release assets. Dry-run by default.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "saymer-alt/mihomo-auto-build"
MARK = "<!-- mipsel-source-errata-20261011 -->"
GOLZO = "github.com/rasky/go-lzo@v0.0.0-20200203143853-96a758eda86e"


class Abort(Exception):
    pass


def gh(args, data=None):
    p = subprocess.run(["gh", *args], input=data, capture_output=True, text=True)
    if p.returncode:
        raise Abort("gh command failed: " + " ".join(args[:4]) + ": " + p.stderr[:300])
    return p.stdout


def get(tag):
    r = json.loads(gh(["api", f"repos/{REPO}/releases/tags/mipsel-{tag}"]))
    if r.get("tag_name") != "mipsel-" + tag or not isinstance(r.get("id"), int):
        raise Abort("Invalid release: " + tag)
    return r


def snapshot(r, tag):
    base = "mihomo-linux-mipsel-softfloat-" + tag
    wanted = {base, base + ".sha256", base + ".LICENSE",
              f"THIRD_PARTY_LICENSES-{tag}.txt", f"THIRD_PARTY_NOTICES-{tag}.txt"}
    items = r.get("assets", [])
    by_name = {x["name"]: x for x in items}
    if not wanted.issubset(by_name) or len(by_name) != len(items):
        raise Abort("Missing/duplicate assets: " + tag)
    for x in items:
        if (x.get("state") != "uploaded" or not isinstance(x.get("id"), int)
                or not isinstance(x.get("size"), int) or x["size"] <= 0
                or not re.fullmatch(r"sha256:[a-f0-9]{64}", x.get("digest") or "")):
            raise Abort("Invalid asset metadata: " + tag)
    return {x["name"]: (x["id"], x["size"], x["digest"]) for x in items}


def asset_text(tag, name, by_name, directory):
    gh(["release", "download", "mipsel-" + tag, "-R", REPO,
        "-p", name, "-D", str(directory)])
    data = (directory / name).read_bytes()
    meta = by_name[name]
    if (len(data) != meta["size"] or
            "sha256:" + hashlib.sha256(data).hexdigest() != meta["digest"]):
        raise Abort("Asset digest mismatch: " + tag + " " + name)
    return data.decode("utf-8")


def go_lzo_label(summary, full):
    matches = [s for s in summary.splitlines()
               if s.startswith("github.com/rasky/go-lzo@") and " | " in s]
    if not matches:
        return None
    if len(matches) != 1 or not matches[0].startswith(GOLZO + " | "):
        raise Abort("Unknown go-lzo version; manual review")
    fields = matches[0].split(" | ")
    if len(fields) < 4 or fields[2] != "LICENSE.gpl" or fields[1] not in ("LGPL-2.1", "GPL-2.0"):
        raise Abort("Unexpected go-lzo license summary row")
    label = fields[1]
    mark = "--- " + GOLZO + " | license: " + label + " | files: LICENSE.gpl"
    if full.count(mark) != 1:
        raise Abort("Full notices not consistent with summary")
    block = full.split(mark, 1)[1].split("\n" + "="*78, 1)[0]
    if "GNU GENERAL PUBLIC LICENSE" not in block or "Version 2, June 1991" not in block:
        raise Abort("Full notice does not prove GPLv2")
    return label


def supplement(tag, digest, label):
    source = "https://github.com/MetaCubeX/mihomo"
    lines = [
        MARK,
        "## Version-pinned source information (2026-10-11)",
        "",
        f"- Upstream source archive: {source}/archive/refs/tags/{tag}.tar.gz",
        f"- Effective Go module metadata: {source}/blob/{tag}/go.mod and {source}/blob/{tag}/go.sum",
        f"- Build/source audit and source-location guide: https://github.com/{REPO}/blob/main/SOURCE-AVAILABILITY.md",
        f"- Open Complete Corresponding Source review: https://github.com/{REPO}/issues/8",
        "",
        "These links alone do not prove the full corresponding source or legal compliance.",
        "The precise historical builder commit and actually linked packages still need verification.",
    ]
    if label == "LGPL-2.1":
        lines += [
            "",
            "### Correction to previously published dependency license summary",
            "",
            f"The original THIRD_PARTY_LICENSES-{tag}.txt incorrectly labels",
            f"{GOLZO} as LGPL-2.1. The pinned source README and LICENSE.gpl",
            "declare GPL version 2; the complete license text in THIRD_PARTY_NOTICES",
            "is GPLv2. The original notice files are retained without replacement.",
            "Whether the module's code is linked into this executable, and any",
            "GPLv2/GPLv3 compatibility effect, remain unverified.",
            f"Original summary digest: {digest}",
            "Reference: https://github.com/rasky/go-lzo/blob/96a758eda86e/LICENSE.gpl",
        ]
    return "\n".join(lines) + "\n"


def plan(tag):
    release = get(tag)
    protected = snapshot(release, tag)
    body = release.get("body")
    if not isinstance(body, str):
        raise Abort("Release body missing")
    by_name = {x["name"]: x for x in release["assets"]}
    summary_name = f"THIRD_PARTY_LICENSES-{tag}.txt"
    full_name = f"THIRD_PARTY_NOTICES-{tag}.txt"
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        summary = asset_text(tag, summary_name, by_name, directory)
        full = asset_text(tag, full_name, by_name, directory)
    label = go_lzo_label(summary, full)
    expected = supplement(tag, by_name[summary_name]["digest"], label)
    if MARK in body:
        if body.count(MARK) != 1 or not body.endswith(expected):
            raise Abort("Prior correction exists but differs: " + tag)
        return release, protected, body, None, label
    return release, protected, body, body.rstrip() + "\n\n" + expected, label


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["plan", "publish"], default="plan")
    args = ap.parse_args()
    queue = []
    for i in range(24, 33):
        tag = "v1.19." + str(i)
        data = plan(tag)
        print(tag, "ADD" if data[3] else "NOOP", "go-lzo:", data[4] or "not listed", flush=True)
        queue.append((tag, data))
    if args.mode == "plan":
        print("DRY RUN PASS; nothing modified")
        return
    for tag, (release, protected, old_body, new_body, _) in queue:
        if new_body is None:
            continue
        live = get(tag)
        if (live["id"] != release["id"] or live.get("body") != old_body
                or snapshot(live, tag) != protected):
            raise Abort("Release changed since preflight: " + tag)
        gh(["api", "--method", "PATCH", f"repos/{REPO}/releases/{release['id']}",
            "--input", "-"], json.dumps({"body": new_body}, ensure_ascii=False))
        after = get(tag)
        if after.get("body") != new_body or snapshot(after, tag) != protected:
            raise Abort("Post-publish identity/content mismatch: " + tag)
        print(tag, "APPENDED AND VERIFIED; assets unchanged", flush=True)
    for tag, _ in queue:
        if plan(tag)[3] is not None:
            raise Abort("Not idempotent: " + tag)
    print("ALL NINE RELEASES VERIFIED; no binary or notice assets changed")


if __name__ == "__main__":
    try:
        main()
    except (Abort, OSError, UnicodeError, ValueError, subprocess.SubprocessError) as exc:
        print("FAIL CLOSED:", exc, file=sys.stderr)
        sys.exit(2)
