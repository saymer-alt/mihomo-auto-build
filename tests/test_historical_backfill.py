# SPDX-License-Identifier: MIT
"""Offline release-integrity guards for manual historical backfill."""
import hashlib
import importlib.util
from pathlib import Path
import unittest

source = Path(__file__).resolve().parents[1] / "scripts" / "historical_backfill.py"
spec = importlib.util.spec_from_file_location("historical_backfill", source)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
DATA = b"never replace the historical published binary"
SHA = "sha256:" + hashlib.sha256(DATA).hexdigest()
VERSION = "1.19.31"
NAMES = m.asset_names(VERSION)


def asset(name, data=DATA, identity=1):
    return {"name": name, "id": identity, "size": len(data),
            "digest": "sha256:" + hashlib.sha256(data).hexdigest(), "state": "uploaded"}


def release():
    return {"id": 42, "tag_name": "mipsel-v" + VERSION, "draft": False,
            "assets": [asset(NAMES[0])]}


class BackfillTests(unittest.TestCase):
    def test_accepted_range_and_rejected_versions(self):
        self.assertEqual(len(m.HISTORIC), 8)
        for v in m.HISTORIC:
            self.assertEqual(m.valid_version(v), v)
        for v in ("1.19.32", "1.19.23", "../1.19.30", "v1.19.31", ""):
            with self.subTest(v=v), self.assertRaises(m.BackfillError):
                m.valid_version(v)

    def test_downloaded_binary_verified_by_real_metadata(self):
        before = m.manifest(release(), VERSION)
        m.check_binary_bytes(before, VERSION, DATA)
        with self.assertRaises(m.BackfillError):
            m.check_binary_bytes(before, VERSION, DATA + b"X")
        with self.assertRaises(m.BackfillError):
            m.check_binary_bytes(before, VERSION, b"different same length"[:len(DATA)])

    def test_four_notice_assets_may_be_added_without_changing_binary(self):
        original = m.manifest(release(), VERSION)
        after_data = release()
        for i, name in enumerate(NAMES[1:], start=2):
            after_data["assets"].append(asset(name, name.encode(), i))
        after = m.manifest(after_data, VERSION)
        m.compare_snapshots(original, after, VERSION)
        with self.assertRaises(m.BackfillError):
            m.compare_snapshots(original, original, VERSION)

    def test_no_binary_replacement_or_foreign_asset_loss(self):
        original = m.manifest(release(), VERSION)
        updated = release()
        for i, name in enumerate(NAMES[1:], start=2):
            updated["assets"].append(asset(name, name.encode(), i))
        updated["assets"][0]["id"] = 999
        with self.assertRaises(m.BackfillError):
            m.compare_snapshots(original, m.manifest(updated, VERSION), VERSION)
        updated["assets"][0]["id"] = 1
        updated["assets"].append(asset("surprise", b"!", 20))
        with self.assertRaises(m.BackfillError):
            m.compare_snapshots(original, m.manifest(updated, VERSION), VERSION)

    def test_malformed_metadata_and_duplicates_fail(self):
        for field, value in [("digest", None), ("size", "42"), ("id", 0),
                             ("state", "starter"), ("name", None)]:
            trial = release()
            trial["assets"][0][field] = value
            with self.subTest(field=field), self.assertRaises(m.BackfillError):
                m.manifest(trial, VERSION)
        dup = release()
        dup["assets"].append(asset(NAMES[0], identity=2))
        with self.assertRaises(m.BackfillError):
            m.manifest(dup, VERSION)


if __name__ == "__main__":
    unittest.main()
