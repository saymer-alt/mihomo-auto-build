# SPDX-License-Identifier: MIT
"""Collect third-party license notices for a released MIPSel binary.

Reproducible from the exact artifact: module identities come from the Go
build information embedded in the binary (go version -m), sources come from
the module proxy at the pinned versions, and licenses are read from the real
files inside those sources - never guessed from names.

Scope and limits (deliberately explicit):
  * The build info lists the module *graph* of the build. The subset of that
    graph whose code is actually linked is smaller; this report deliberately
    over-includes so obligations are reviewed conservatively.
  * Classification is phrase-based heuristics over real license files. It is
    evidence for human review, **not a legal conclusion**. Copyleft findings
    (GPL/LGPL/MPL) are escalations, never a completed distribution strategy.

Outputs:
  summary file  - compact module -> license table (reviewable, committed)
  full notices  - complete license texts, shipped alongside the binary

Fail-closed: a module without at least one recognized LICENSE/COPYING file,
an unparseable response, or an unreadable file exits non-zero.
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
    """Parse `go version -m` output.

    Returns (main, modules): `main` is (import_path, version) of the built
    module; `modules` maps import_path -> [source_path, version]. A replace
    directive changes the source location but not the import path.
    """
    main, modules, current = None, {}, None
    for line in text.splitlines():
        mod = re.match(r"\tmod\t(\S+)\t(\S+)", line)
        if mod:
            main = (mod.group(1), mod.group(2))
        dep = re.match(r"\tdep\t(\S+)\t(\S+)", line)
        if dep:
            current = dep.group(1)
            modules[current] = [current, dep.group(2)]
        repl = re.match(r"\t=>\t(\S+)\t(\S+)", line)
        if repl and current:
            modules[current] = [repl.group(1), repl.group(2)]
    return main, modules


def build_modules(binary):
    out = run_go(["version", "-m", str(binary)])
    main, modules = parse_build_info(out)
    if not modules or main is None:
        raise CollectError("No dependency build info found in the binary")
    return main, modules


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
    # Standard ISC and a documented historical variant (coder/websocket v1.8.12)
    # use "and/or distribute" vs "and distribute"; both require fee-free
    # permission and retention of the original copyright notice.
    if ("with or without fee" in low and "copyright notice" in low and
            any(phrase in low for phrase in (
                "permission to use, copy, modify, and/or distribute this software",
                "permission to use, copy, modify, and distribute this software"))):
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


def mod_dir(source_path, ver):
    cache = run_go(["env", "GOMODCACHE"]).strip()
    escaped = re.sub(r"([A-Z])", lambda m: "!" + m.group(1).lower(), source_path)
    for candidate in (Path(cache) / f"{source_path}@{ver}", Path(cache) / f"{escaped}@{ver}"):
        if candidate.is_dir():
            return candidate
    return None


def license_files(directory):
    """Root-level license files first; otherwise one subdirectory level,
    complete - never an arbitrary single file from an unknown depth."""
    root, sub = [], []
    for entry in sorted(directory.iterdir()):
        if entry.is_file() and LICENSE_RE.match(entry.name):
            root.append(entry)
    if root:
        return root
    for child in sorted(directory.iterdir()):
        if child.is_dir() and child.name not in (".git", "testdata", "examples", "docs"):
            sub.extend(e for e in sorted(child.iterdir())
                       if e.is_file() and LICENSE_RE.match(e.name))
    return sub


def collect_module(import_path, source_path, ver, label=None):
    run_go(["mod", "download", f"{source_path}@{ver}"])
    d = mod_dir(source_path, ver)
    key = label or f"{import_path}@{ver}"
    if d is None:
        return {"status": "missing-source", "key": key, "module": import_path,
                "version": ver, "source": source_path}
    files = license_files(d)
    if not files:
        return {"status": "no-license-file", "key": key, "module": import_path,
                "version": ver, "source": source_path}
    licenses, texts, copyright_line = set(), {}, None
    for f in files:
        try:
            text = f.read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            return {"status": "unreadable-license", "key": key, "module": import_path,
                    "version": ver, "source": source_path, "file": f.name,
                    "error": str(exc)[:200]}
        texts[f.name] = text
        if LICENSE_ONLY_RE.match(f.name):
            kind = classify(text)
            if kind is None:
                return {"status": "unrecognized-license", "key": key,
                        "module": import_path, "version": ver, "source": source_path,
                        "file": f.name}
            licenses.add(kind)
        if copyright_line is None:
            m = re.search(r"^(?:Copyright|©|SPDX-FileCopyrightText:).*$", text, re.M)
            if m:
                copyright_line = m.group(0).strip()
    if not licenses:
        # Only NOTICE/COPYRIGHT/PATENTS companions were found: the module's
        # actual license is undetermined. Never report success for this.
        return {"status": "no-classified-license", "key": key, "module": import_path,
                "version": ver, "source": source_path, "files": sorted(texts)}
    return {"status": "ok", "key": key, "module": import_path, "version": ver,
            "source": source_path, "license": sorted(licenses),
            "files": sorted(texts), "copyright": copyright_line, "texts": texts}


def collect_all(binary):
    """Collect the upstream main module plus every dependency module."""
    main, modules = build_modules(binary)
    results = {}
    main_path, main_ver = main
    results[f"{main_path}@{main_ver}"] = collect_module(
        main_path, main_path, main_ver, label=f"{main_path}@{main_ver} [upstream main module]")
    for import_path, (source_path, ver) in sorted(modules.items()):
        results[f"{import_path}@{ver}"] = collect_module(import_path, source_path, ver)
    return results


def main_version(binary):
    return build_modules(binary)[0][1]


def key_line(r):
    """Rendered module key; replaced modules carry their source identity."""
    line = r["key"]
    if r["source"] != r["module"]:
        line += f" [source: {r['source']}@{r['version']}]"
    return line


def render_summary(version, results):
    lines = [
        f"Third-party license summary for Mihomo {version} (MIPSel rebuild).",
        "Generated from the released binary's Go build information; licenses",
        "were read from the real upstream files at the pinned module versions.",
        "",
        "This table is heuristic evidence for human review, not a legal",
        "conclusion; it lists the build module graph, which over-includes the",
        "actually linked code on purpose. Copyleft findings are escalations.",
        "",
        "module@version | license | files | copyright",
    ]
    unresolved = []
    for r in results.values():
        if r["status"] != "ok":
            unresolved.append(r)
            continue
        lines.append(" | ".join((
            key_line(r), "+".join(r["license"]), ",".join(r["files"]),
            r["copyright"] or "-")))
    for r in sorted(unresolved, key=lambda x: x["key"]):
        lines.append(f"UNRESOLVED {key_line(r)} | {r['status']}"
                     + (f" | {r.get('error', '')}" if r.get("error") else ""))
    lines.append("")
    copyleft = sorted((r for r in results.values() if r["status"] == "ok"
                       and any(l.startswith(COPYLEFT) for l in r["license"])),
                      key=lambda r: r["key"])
    lines.append(f"copyleft indicators (GPL/LGPL/MPL), escalate for legal review: {len(copyleft)}")
    for r in copyleft:
        lines.append(f"  {key_line(r)} -> {'+'.join(r['license'])}")
    lines.append("")
    lines.append("Full license texts are produced as THIRD_PARTY_NOTICES-<version>.txt")
    lines.append("and must accompany any redistribution of the binary. Source code")
    lines.append("for every module is available at its module path and version")
    lines.append("through the Go module proxy (proxy.golang.org); the upstream")
    lines.append("corresponding source for the binary is the tagged upstream tree")
    lines.append("plus this repository's build scripts.")
    return "\n".join(lines) + "\n", [r["key"] for r in unresolved]


def render_full(version, results):
    parts = [
        f"THIRD-PARTY SOFTWARE NOTICES for Mihomo {version} (MIPSel rebuild)",
        "",
        "This document contains license texts for the upstream Mihomo module",
        "and for the Go module graph of the released binary. It over-includes",
        "the actually linked code deliberately; classification is heuristic",
        "evidence for human review, not a legal conclusion. Module identities",
        "and versions come from the binary's build info; texts are verbatim",
        "copies of the upstream files at those versions.",
        "",
        "=" * 78, "",
    ]
    for key in sorted(results):
        r = results[key]
        if r["status"] != "ok":
            continue
        header = f"--- {key_line(r)} | license: {'+'.join(r['license'])} | files: {','.join(r['files'])}"
        parts.append(header)
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
    parser.add_argument("--report", help="optional JSON report path")
    args = parser.parse_args()
    binary = Path(args.binary)
    if not binary.is_file() or binary.stat().st_size == 0:
        raise CollectError("Binary is missing or empty")
    results = collect_all(binary)
    unresolved = [r["key"] for r in results.values() if r["status"] != "ok"]
    version = main_version(binary)
    summary, _ = render_summary(version, results)
    Path(args.summary).write_text(summary, encoding="utf-8")
    Path(args.full).write_text(render_full(version, results), encoding="utf-8")
    if args.report:
        slim = {k: {f: v.get(f) for f in ("status", "module", "version", "source",
                                          "license", "files", "copyright")}
                for k, v in results.items()}
        Path(args.report).write_text(json.dumps(
            {"version": version, "modules": slim, "unresolved": unresolved},
            indent=1), encoding="utf-8")
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
