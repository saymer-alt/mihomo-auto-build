# SPDX-License-Identifier: MIT
"""Read-only MIPSel package graph and *unstripped* Go linker-symbol audit.

This is not proof that a historic, stripped Release binary contains identical
linked symbols. Does not build or publish release assets.
"""
import argparse
from collections import deque
import json
from pathlib import Path
import re

TARGET = "github.com/rasky/go-lzo"


def parse_go_list(text):
    decoder = json.JSONDecoder()
    packages = {}
    pos = 0
    while pos < len(text):
        while pos < len(text) and text[pos].isspace():
            pos += 1
        if pos == len(text):
            break
        data, pos = decoder.raw_decode(text, pos)
        if "ImportPath" not in data or not isinstance(data.get("Imports", []), list):
            raise ValueError("Invalid go list package object")
        path = data["ImportPath"]
        if path in packages:
            raise ValueError("Duplicate package " + path)
        module = data.get("Module") or {}
        packages[path] = {
            "imports": data.get("Imports", []),
            "module": module.get("Path"),
            "go_files": data.get("GoFiles", []),
        }
    if not packages:
        raise ValueError("No packages in go list -deps -json output")
    return packages


def shortest_chain(packages, main, target=TARGET):
    if main not in packages:
        raise ValueError("Main package not in Go import graph")
    queue = deque([(main,)])
    visited = {main}
    while queue:
        chain = queue.popleft()
        path = chain[-1]
        if packages[path]["module"] == target or path == target or path.startswith(target + "/"):
            return list(chain)
        for dependency in packages[path]["imports"]:
            if dependency in packages and dependency not in visited:
                visited.add(dependency)
                queue.append(chain + (dependency,))
    return []


def symbol_names(text, target=TARGET):
    # Go 'nm' on an unstripped ELF returns address/size/type/symbol.
    # Match exact package path; other modules merely mentioning this text
    # are not proof of actual functions kept by the linker.
    names = set()
    for line in text.splitlines():
        match = re.match(r"^\s*[0-9a-fA-F]+\s+\d+\s+[A-Za-z?]\s+(\S+)$", line)
        if not match:
            match = re.match(r"^\s*[0-9a-fA-F]+\s+[A-Za-z?]\s+(\S+)$", line)
        if match:
            sym = match.group(1)
            if sym.startswith(target + ".") or sym.startswith(target + "/"):
                names.add(sym)
    return sorted(names)


def report(packages, symbols, main):
    chain = shortest_chain(packages, main)
    imported = [p for p, d in packages.items()
                if d["module"] == TARGET or p == TARGET or p.startswith(TARGET + "/")]
    return {
        "target": TARGET,
        "main": main,
        "package_count": len(packages),
        "target_package_count": len(imported),
        "target_packages": sorted(imported),
        "shortest_import_chain": chain,
        "unstripped_linker_symbol_count": len(symbols),
        "unstripped_linker_symbol_sample": symbols[:40],
        "symbol_evidence_note": (
            "Symbols from a diagnostic unstripped rebuild at the pinned "
            "upstream version and Go toolchain. NOT a byte-identical "
            "reconstruction or symbol map of the published stripped binary."
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--go-list", type=Path, required=True)
    parser.add_argument("--nm", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--main", default="github.com/metacubex/mihomo")
    args = parser.parse_args()
    packs = parse_go_list(args.go_list.read_text(encoding="utf-8"))
    names = symbol_names(args.nm.read_text(encoding="utf-8"))
    data = report(packs, names, args.main)
    args.out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    if not data["shortest_import_chain"] or not data["target_packages"]:
        raise SystemExit("Target module absent from selected package graph (guard evidence needs updating)")


if __name__ == "__main__":
    main()
