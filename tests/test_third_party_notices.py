# SPDX-License-Identifier: MIT
"""Offline validation of the committed third-party license summary."""
import importlib.util
import re
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "go-buildinfo-v1.19.32.txt"
SUMMARY = ROOT / "THIRD_PARTY_LICENSES-v1.19.32.txt"

spec = importlib.util.spec_from_file_location(
    "collect_licenses", ROOT / "scripts" / "collect_upstream_licenses.py")
cl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cl)


def parse_fixture():
    """Replay the collector's parser over the committed build info."""
    modules, current = {}, None
    for line in FIXTURE.read_text(encoding="utf-8").splitlines():
        dep = re.match(r"\tdep\t(\S+)\t(\S+)", line)
        if dep:
            current = dep.group(1)
            modules[current] = dep.group(2)
        repl = re.match(r"\t=>\t(\S+)\t(\S+)", line)
        if repl and current:
            modules[current] = repl.group(2)
    return modules


class ThirdPartyNotices(unittest.TestCase):
    def setUp(self):
        self.summary = SUMMARY.read_text(encoding="utf-8")
        self.expected = parse_fixture()

    def test_summary_covers_every_effective_module(self):
        covered = {
            m.group(1)
            for m in re.finditer(r"^([^\s|]+@\S+) \| ", self.summary, re.M)}
        expected_keys = {f"{mod}@{ver}" for mod, ver in self.expected.items()}
        missing = expected_keys - covered
        self.assertFalse(missing, f"summary lacks modules: {sorted(missing)}")

    def test_no_unresolved_entries(self):
        self.assertNotIn("UNRESOLVED", self.summary)

    def test_every_module_has_recognized_license(self):
        for m in re.finditer(r"^([^\s|]+@\S+) \| ([^|]+) \| ", self.summary, re.M):
            if m.group(1) == "module@version":
                continue  # table header
            for kind in m.group(2).strip().split("+"):
                self.assertRegex(kind, r"^(Apache-2\.0|MIT|ISC|BSD-[234]-Clause|MPL-2\.0"
                                       r"|LGPL-[23]\.[0-9]|GPL-[23]\.0(-or-later)?"
                                       r"|CC0-1\.0|BSL-1\.0|Unlicense|Zlib)$",
                                 f"{m.group(1)}: {kind}")

    def test_copyleft_modules_are_flagged(self):
        copyleft = re.findall(r"^  (\S+) -> (.+)$", self.summary, re.M)
        self.assertTrue(copyleft, "copyleft section missing")
        declared = dict(copyleft)
        counted = re.findall(r"^([^\s|]+@\S+) \| ([^|]+) \| ", self.summary, re.M)
        expected = {k: v for k, v in counted
                    if any(l.startswith(("GPL", "LGPL", "MPL")) for l in v.split("+"))}
        self.assertEqual(declared, expected,
                         "copyleft section must match module license fields")
        header = re.search(r"copyleft modules \(GPL/LGPL/MPL\): (\d+)", self.summary)
        self.assertEqual(int(header.group(1)), len(expected))

    def test_summary_states_the_fixture_version(self):
        main_line = re.search(r"^\tmod\t\S+\t(\S+)", FIXTURE.read_text(encoding="utf-8"), re.M)
        self.assertIn(f"for Mihomo {main_line.group(1)}", self.summary)

    def test_build_info_parser_handles_replace_directives(self):
        # The collector parser and this fixture's parser must agree, including
        # replace directives: sources come from the replacement module.
        sample = ("\tmod\tgithub.com/metacubex/mihomo\tv1.19.32\n"
                  "\tdep\tgoogle.golang.org/protobuf\tv1.34.2\n"
                  "\t=>\tgithub.com/metacubex/protobuf-go\tv0.0.0-fix\n"
                  "\tdep\tgithub.com/example/plain\tv2.0.0\n")
        parsed = cl.parse_build_info(sample)
        self.assertEqual(parsed["google.golang.org/protobuf"],
                         ["github.com/metacubex/protobuf-go", "v0.0.0-fix"])
        self.assertEqual(parsed["github.com/example/plain"],
                         ["github.com/example/plain", "v2.0.0"])


if __name__ == "__main__":
    unittest.main()
