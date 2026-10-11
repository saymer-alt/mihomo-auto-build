# SPDX-License-Identifier: MIT
"""Regression tests for append-only historical source/errata notes."""
import importlib.util
from pathlib import Path
import unittest

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "notes", root / "scripts" / "update_release_source_notes.py")
notes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notes)


class ErrataTests(unittest.TestCase):
    def test_known_gplv2_mislabeled_row(self):
        label = "LGPL-2.1"
        row = notes.GOLZO + " | " + label + " | LICENSE.gpl | -\n"
        notice = ("--- " + notes.GOLZO + " | license: " + label
                  + " | files: LICENSE.gpl\n"
                  + "GNU GENERAL PUBLIC LICENSE\nVersion 2, June 1991\n\n"
                  + "=" * 78 + "\n")
        self.assertEqual(notes.go_lzo_label(row, notice), label)
        text = notes.supplement("v1.19.32", "sha256:" + "a"*64, label)
        self.assertIn("GPL version 2", text)
        self.assertIn(notes.MARK, text)
        self.assertIn("96a758eda86e/LICENSE.gpl", text)

    def test_module_absence_does_not_invent_erratum(self):
        self.assertIsNone(notes.go_lzo_label("other | MIT | LICENSE | -\n", ""))
        note = notes.supplement("v1.19.24", "sha256:" + "b"*64, None)
        self.assertIn("v1.19.24.tar.gz", note)
        self.assertNotIn("Correction to previously", note)

    def test_unknown_version_and_wrong_full_license_refused(self):
        with self.assertRaises(notes.Abort):
            notes.go_lzo_label("github.com/rasky/go-lzo@v9 | LGPL-2.1 | LICENSE.gpl | -", "")
        with self.assertRaises(notes.Abort):
            notes.go_lzo_label(
                notes.GOLZO + " | LGPL-2.1 | LICENSE.gpl | -",
                "--- " + notes.GOLZO + " | license: LGPL-2.1 | files: LICENSE.gpl\n"
                "GNU LESSER GENERAL PUBLIC LICENSE\nVersion 3, 29 June 2007\n")

    def test_asset_manifest_guards(self):
        version = "v1.19.32"
        base = "mihomo-linux-mipsel-softfloat-" + version
        names = [base, base + ".sha256", base + ".LICENSE",
                 f"THIRD_PARTY_LICENSES-{version}.txt",
                 f"THIRD_PARTY_NOTICES-{version}.txt"]
        assets = [{"name": name, "id": idx+1, "size": 12, "state": "uploaded",
                   "digest": "sha256:"+"f"*64}
                  for idx, name in enumerate(names)]
        self.assertEqual(len(notes.snapshot({"assets": assets}, version)), 5)
        assets[0]["size"] = 0
        with self.assertRaises(notes.Abort):
            notes.snapshot({"assets": assets}, version)


if __name__ == "__main__":
    unittest.main()
