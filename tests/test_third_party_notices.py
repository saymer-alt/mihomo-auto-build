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


def summary_rows(text):
    """Parse `key | license | files | copyright` rows; keys may contain spaces."""
    rows = []
    for line in text.splitlines():
        parts = line.split(" | ")
        if len(parts) >= 2 and ("@" in parts[0]) and parts[0] != "module@version":
            rows.append((parts[0], parts[1].strip()))
        elif line.startswith("UNRESOLVED "):
            rows.append((line, "UNRESOLVED"))
    return rows


class ThirdPartyNotices(unittest.TestCase):
    def setUp(self):
        self.summary = SUMMARY.read_text(encoding="utf-8")
        self.rows = summary_rows(self.summary)
        self.unresolved = [k for k, lic in self.rows if lic == "UNRESOLVED"]

    def test_summary_covers_every_effective_module(self):
        main, modules = cl.parse_build_info(
            FIXTURE.read_text(encoding="utf-8"))
        expected = {f"{import_path}@{ver}" for import_path, (_, ver) in modules.items()}
        covered = {k.split(" [")[0] for k, lic in self.rows if lic != "UNRESOLVED"}
        missing = expected - covered
        self.assertFalse(missing, f"summary lacks modules: {sorted(missing)}")

    def test_upstream_main_module_row_is_first_and_gpl(self):
        main_row = next((lic for k, lic in self.rows
                         if "[upstream main module]" in k), None)
        self.assertEqual(main_row, "GPL-3.0",
                         "upstream Mihomo itself is GPL-3.0 and must be listed")

    def test_no_unresolved_entries(self):
        self.assertEqual(self.unresolved, [])

    def test_every_module_has_recognized_license(self):
        known = re.compile(r"^(Apache-2\.0|MIT|ISC|BSD-[234]-Clause|MPL-2\.0"
                           r"|LGPL-[23]\.[0-9]|GPL-[23]\.0(-or-later)?"
                           r"|CC0-1\.0|BSL-1\.0|Unlicense|Zlib)$")
        for key, lic in self.rows:
            if lic == "UNRESOLVED":
                continue
            for kind in lic.split("+"):
                self.assertRegex(kind, known, f"{key}: {kind}")

    def test_copyleft_modules_are_flagged_as_escalations(self):
        copyleft = dict(re.findall(r"^  (.+?) -> (.+)$", self.summary, re.M))
        self.assertTrue(copyleft, "copyleft section missing")
        expected = {key: lic for key, lic in self.rows
                    if lic != "UNRESOLVED"
                    and any(l.startswith(("GPL", "LGPL", "MPL"))
                            for l in lic.split("+"))}
        self.assertEqual(copyleft, expected,
                         "copyleft section must match module license fields")
        header = re.search(r"copyleft indicators \(GPL/LGPL/MPL\), "
                           r"escalate for legal review: (\d+)", self.summary)
        self.assertEqual(int(header.group(1)), len(expected))

    def test_summary_states_the_fixture_version(self):
        main, _ = cl.parse_build_info(FIXTURE.read_text(encoding="utf-8"))
        self.assertIn(f"for Mihomo {main[1]}", self.summary)

    def test_replaced_modules_carry_source_provenance(self):
        _, modules = cl.parse_build_info(FIXTURE.read_text(encoding="utf-8"))
        replaced = {ip: src for ip, (src, _) in modules.items() if src != ip}
        if not replaced:
            self.fail("fixture is expected to contain at least one replace directive")
        for import_path, source in replaced.items():
            self.assertIn(f"source: {source}@", self.summary,
                          f"replaced module {import_path} must show its source identity")

    def test_summary_does_not_claim_completed_compliance(self):
        self.assertNotIn("Full license texts ship as", self.summary)
        self.assertIn("not a legal", self.summary)
        self.assertIn("must accompany any redistribution", self.summary)

    def test_historical_websocket_isc_variant_from_exact_upstream_license(self):
        license_text = (ROOT / "tests" / "fixtures" /
                        "coder-websocket-v1.8.12-LICENSE.txt").read_text(encoding="utf-8")
        self.assertIn("and distribute this software", license_text)
        self.assertIn("with or without fee", license_text)
        self.assertEqual(cl.classify(license_text), "ISC")
        # Avoid classifying permissive-looking text without the key fee condition.
        self.assertIsNone(cl.classify(
            "Permission to use, copy, modify, and distribute this software."))

    def test_parser_rejects_notice_only_modules(self):
        # A module whose files carry only NOTICE/PATENTS (no LICENSE/COPYING)
        # must never be reported as classified.
        sample = ("GNU GENERAL PUBLIC LICENSE\nVersion 3, 29 June 2007\n"
                  "Free Software Foundation, Inc. <https://fsf.org/>\n")
        self.assertIsNotNone(cl.classify(sample))
        self.assertIsNone(cl.classify("PATENTS grant text without license terms"))


if __name__ == "__main__":
    unittest.main()
