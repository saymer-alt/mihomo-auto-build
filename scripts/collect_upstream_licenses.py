# SPDX-License-Identifier: MIT
"""Collect third-party license notices for a released MIPSel binary.

Reproducible from the exact artifact: module identities come from the Go
build information embedded in the binary (go version -m), sources come from
the module proxy at the pinned versions, and licenses are read from the real
files inside those sources - never guessed from names.

Outputs:
  summary file  - compact module -> license table (reviewable, committed)
  full notices  - complete license texts, shipped as a release asset

Fail-closed: an unresolvable or ambiguous license exits non-zero.
Requires: go on PATH and network access to the module proxy.

Usage:
  python3 scripts/collect_upstream_licenses.py --binary <bin> \
      --summary THIRD_PARTY_LICENSES-<ver>.txt \
      --full THIRD_PARTY_NOTICES-<ver>.txt
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

COPYLEFT = ("GPL", "LGPL", "MPL", "AGPL")
LICENSE_RE = re.compile(r"^(LICENSE|LICENCE|COPYING|COPYRIGHT|NOTICE|PATENTS)([._-].*)?$", re.I)
LICENSE_ONLY_RE = re.compile(r"^(LICENSE|LICENCE|COPYING)([._-][A-Za-z0-9]+)?$", re.I)


class CollectError(Exception):
    pass


def run_go(args):
    result = subprocess.run(["go", *args], capture_output=True, text=True)
    if result.returncode:
        raise CollectError(f"go {' '.join(args)} failed: {result.stderr.strip()[:400]}")
    return result.stdout


def parse_build_info(text):
    """Parse `go version -m` output into {import_path: [source_path, version]}.

    A replace directive changes the source location but not the import path.
    """
    modules, current = {}, None
    for line in text.splitlines():
        dep = re.match(r"\tdep\t(\S+)\t(\S+)", line)
        if dep:
            current = dep.group(1)
            modules[current] = [current, dep.group(2)]
        repl = re.match(r"\t=>\t(\S+)\t(\S+)", line)
        if repl and current:
            modules[current] = [repl.group(1), repl.group(2)]
    return modules


def build_modules(binary):
    """Effective module list from the binary's embedded build information."""
    out = run_go(["version", "-m", str(binary)])
    modules = parse_build_info(out)
    if not modules:
        raise CollectError("No dependency build info found in the binary")
    return modules


def classify(text):
    t = text[:8000]
    low = t.lower()
    if "apache license" in low and "version 2.0, january 2004" in low:
        return "Apache-2.0"
    if "permission is hereby granted, free of charge" in low:
        return "MIT"
    if "mozilla public license" in low and "2.0" in t:
        return "MPL-2.0"
    if "redistribution and use in source and binary forms" in low:
        if "all advertising materials mentioning features" in low:
            return "BSD-4-Clause"
        if ("neither the name of" in low or "neither be used" in low
                or "may not be used to endorse" in low):
            return "BSD-3-Clause"
        return "BSD-2-Clause"
    if "permission to use, copy, modify, and/or distribute this software" in low:
        return "ISC"
    if "gnu lesser general public license" in low:
        return "LGPL-3.0" if "version 3" in low else "LGPL-2.1"
    if "gnu general public license" in low:
        if "version 2, june 1991" in low:
            return "GPL-2.0" if "or later" not in low else "GPL-2.0-or-later"
        if "version 3, 29 june 2007" in low:
            return "GPL-3.0" if "or later" not in low else "GPL-3.0-or-later"
    if "this program is free software" in low and "gnu general public license" in low:
        return "GPL-3.0-or-later" if "any later version" in low else "GPL-license-notice-unresolved"
    if "this is free and unencumbered software released into the public domain" in low:
        return "Unlicense"
    if "cc0 1.0 universal" in low:
        return "CC0-1.0"
    if "boost software license" in low:
        return "BSL-1.0"
    return None


def mod_dir(mod, ver):
    cache = run_go(["env", "GOMODCACHE"]).strip()
    escaped = re.sub(r"([A-Z])", lambda m: "!" + m.group(1).lower(), mod)
    for candidate in (Path(cache) / f"{mod}@{ver}", Path(cache) / f"{escaped}@{ver}"):
        if candidate.is_dir():
            return candidate
    return None


def collect_module(import_path, source_path, ver):
    run_go(["mod", "download", f"{source_path}@{ver}"])
    d = mod_dir(source_path, ver)
    if d is None:
        return {"status": "missing-source", "module": import_path, "version": ver,
                "source": source_path}
    files = []
    for root, dirs, names in os.walk(d):
        dirs[:] = [x for x in dirs if x not in (".git", "testdata", "examples", "docs")]
        files.extend(os.path.join(root, n) for n in names if LICENSE_RE.match(n))
        if files and root != str(d):
            break
    top = [f for f in files if os.path.dirname(f) == str(d)] or files[:1]
    if not top:
        return {"status": "no-license-file", "module": import_path, "version": ver,
                "source": source_path}
    licenses, texts, copyright_line = set(), {}, None
    for f in top:
        try:
            raw = Path(f).read_bytes()
            text = raw.decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            return {"status": "unreadable-license", "module": import_path, "version": ver,
                    "source": source_path, "file": os.path.basename(f),
                    "error": str(exc)[:200]}
        name = os.path.basename(f)
        texts[name] = text
        if LICENSE_ONLY_RE.match(name):
            kind = classify(text)
            if kind is None:
                return {"status": "unrecognized-license", "module": import_path,
                        "version": ver, "source": source_path, "file": name}
            licenses.add(kind)
        if copyright_line is None:
            m = re.search(r"^(?:Copyright|©|SPDX-FileCopyrightText:).*$", text, re.M)
            if m:
                copyright_line = m.group(0).strip()
    return {"status": "ok", "module": import_path, "version": ver, "source": source_path,
            "license": sorted(licenses), "files": sorted(texts),
            "copyright": copyright_line, "texts": texts}


def collect_all(binary):
    modules = build_modules(binary)
    results = {}
    for import_path, (source_path, ver) in sorted(modules.items()):
        results[f"{import_path}@{ver}"] = collect_module(import_path, source_path, ver)
    return results


def main_version(binary):
    out = run_go(["version", "-m", str(binary)])
    m = re.search(r"^\tmod\t\S+\t(\S+)", out, re.M)
    if not m:
        raise CollectError("Binary lacks module build info; cannot determine version")
    return m.group(1)


def render_summary(version, results):
    lines = [
        f"Third-party license summary for Mihomo {version} (MIPSel rebuild).",
        "Generated from the released binary's Go build information; licenses",
        "were read from the real upstream files at the pinned module versions.",
        "",
        "unique-counts are not applicable here; one line per effective module.",
        "",
        "module@version | license | files | copyright",
    ]
    unresolved = []
    for key, r in results.items():
        if r["status"] != "ok":
            unresolved.append(key)
            continue
        lines.append(" | ".join((
            key, "+".join(r["license"]), ",".join(r["files"]), r["copyright"] or "-")))
    for key in sorted(unresolved):
        r = results[key]
        lines.append(f"UNRESOLVED {key} | {r['status']}")
    lines.append("")
    copyleft = sorted(k for k, r in results.items() if r["status"] == "ok"
                      and any(l.startswith(COPYLEFT) for l in r["license"]))
    lines.append(f"copyleft modules (GPL/LGPL/MPL): {len(copyleft)}")
    for key in copyleft:
        lines.append(f"  {key} -> {'+'.join(results[key]['license'])}")
    lines.append("")
    lines.append("The statically linked binary redistributes these components.")
    lines.append("Full license texts ship as THIRD_PARTY_NOTICES-<version>.txt.")
    lines.append("Source code for every module is available at its module path")
    lines.append("and version through the Go module proxy (proxy.golang.org).")
    return "\n".join(lines) + "\n", unresolved


def render_full(version, results):
    parts = [
        f"THIRD-PARTY SOFTWARE NOTICES for Mihomo {version} (MIPSel rebuild)",
        "",
        "This document contains license notices for the Go modules whose",
        "object code is statically linked into the distributed binary.",
        "Module identities and versions come from the binary's build info;",
        "texts are verbatim copies of the upstream files at those versions.",
        "",
        "=" * 78, "",
    ]
    for key in sorted(results):
        r = results[key]
        if r["status"] != "ok":
            continue
        parts.append(f"--- {key} | license: {'+'.join(r['license'])} "
                     f"| files: {','.join(r['files'])} ---")
        for name in sorted(r["texts"]):
            parts.append(r["texts"][name].rstrip("\n"))
        parts.append("")
        parts.append("=" * 78)
        parts.append("")
    return "\n".join(parts) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", required=True, help="released MIPSel binary")
    parser.add_argument("--summary", required=True)
    parser.add_argument("--full", required=True)
    args = parser.parse_args()
    binary = Path(args.binary)
    if not binary.is_file() or binary.stat().st_size == 0:
        raise CollectError("Binary is missing or empty")
    results = collect_all(binary)
    unresolved = [k for k, r in results.items() if r["status"] != "ok"]
    version = main_version(binary)
    summary, _ = render_summary(version, results)
    Path(args.summary).write_text(summary, encoding="utf-8")
    Path(args.full).write_text(render_full(version, results), encoding="utf-8")
    print(f"version={version} modules={len(results)} unresolved={len(unresolved)}")
    for key in sorted(unresolved):
        print(f"UNRESOLVED {key} status={results[key]['status']}", file=sys.stderr)
    if unresolved:
        raise CollectError("Unresolved modules must be reviewed by a human")


if __name__ == "__main__":
    try:
        main()
    except (CollectError, OSError, ValueError) as error:
        print(f"License collection failed: {error}", file=sys.stderr)
        sys.exit(2)
