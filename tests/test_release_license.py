# SPDX-License-Identifier: MIT
"""Offline verification of upstream license publication and fail-closed guards."""
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import release_license as lic
from test_release_assets import BIN, TAG, DATA, Fake


MIT_FIXTURE = (b"Copyright 2023 KT\nPermission is hereby granted\n"
               b"THE SOFTWARE IS PROVIDED\n" + b"license notice text\n" * 15)


class LicenseTests(unittest.TestCase):
    def test_upload_then_rerun_preserves_binary_and_checksum(self):
        api = Fake(side=True)
        originals = list(api.release["assets"])
        self.assertTrue(lic.ensure_license(api, "owner/repo", TAG, BIN, MIT_FIXTURE))
        self.assertEqual(api.release["assets"][:2], originals)
        self.assertEqual(lic.license_name(BIN), BIN + ".LICENSE")
        before = list(api.release["assets"])
        self.assertFalse(lic.ensure_license(api, "owner/repo", TAG, BIN, MIT_FIXTURE))
        self.assertEqual(before, api.release["assets"])
        self.assertFalse(any(method == "DELETE" for method, _ in api.calls))
        self.assertNotIn(("UPLOAD", BIN), api.calls)
        self.assertNotIn(("UPLOAD", BIN + ".sha256"), api.calls)

    def test_checksum_missing_or_binary_missing_refuses_notice(self):
        for api in (Fake(), Fake(binary=None)):
            with self.assertRaisesRegex(lic.assets.MetadataError, "must be complete"):
                lic.ensure_license(api, "owner/repo", TAG, BIN, MIT_FIXTURE)
            self.assertFalse(any(x[0] in ("UPLOAD", "DELETE") for x in api.calls))

    def test_invalid_or_conflicting_notice_fails_closed(self):
        for bytes_ in (b"different", b"", MIT_FIXTURE + b"bad"):
            api = Fake(side=True)
            api.add(BIN + ".LICENSE", bytes_)
            before = list(api.release["assets"])
            with self.assertRaises(lic.assets.MetadataError):
                lic.ensure_license(api, "owner/repo", TAG, BIN, MIT_FIXTURE)
            self.assertEqual(before, api.release["assets"])
            self.assertFalse(any(x[0] in ("UPLOAD", "DELETE") for x in api.calls))

    def test_duplicate_and_starter_notice_refused(self):
        for make in ("duplicate", "starter"):
            api = Fake(side=True)
            api.add(BIN + ".LICENSE", MIT_FIXTURE)
            if make == "duplicate":
                api.release["assets"].append(dict(api.release["assets"][-1], id=777))
            else:
                api.release["assets"][-1].update(size=0, state="starter", digest=None)
            with self.assertRaises(lic.assets.MetadataError):
                lic.ensure_license(api, "owner/repo", TAG, BIN, MIT_FIXTURE)
            self.assertFalse(any(x[0] in ("UPLOAD", "DELETE") for x in api.calls))

    def test_failed_upload_retry_preserves_existing_assets(self):
        api = Fake(side=True)
        original = list(api.release["assets"])
        api.fail_upload = True
        with self.assertRaises(Exception):
            lic.ensure_license(api, "owner/repo", TAG, BIN, MIT_FIXTURE)
        self.assertEqual(api.release["assets"], original)
        api.fail_upload = False
        self.assertTrue(lic.ensure_license(api, "owner/repo", TAG, BIN, MIT_FIXTURE))

    def test_invalid_tag_or_license_refused_before_mutation(self):
        api = Fake(side=True)
        for wrongtag, wrongbin, notice in (
            (TAG, BIN + "-another", MIT_FIXTURE),
            ("mipsel-v1.19.32/../../main", BIN, MIT_FIXTURE),
            (TAG, BIN, b"not upstream"),
        ):
            with self.assertRaises(lic.assets.MetadataError):
                lic.ensure_license(api, "owner/repo", wrongtag, wrongbin, notice)
        self.assertFalse(any(x[0] in ("UPLOAD", "DELETE") for x in api.calls))

    def test_license_fetched_from_exact_upstream_tag(self):
        with patch.object(lic, "urlopen", return_value=io.BytesIO(MIT_FIXTURE)) as mocked:
            self.assertEqual(lic.download_tagged_license(TAG), MIT_FIXTURE)
            self.assertEqual(mocked.call_args.args[0],
                             "https://raw.githubusercontent.com/MetaCubeX/mihomo/v1.19.32/LICENSE")
        with self.assertRaises(lic.assets.MetadataError):
            lic.download_tagged_license("mipsel-v1.19.32/../../main")

    def test_foreign_release_assets_unchanged(self):
        api = Fake(side=True)
        api.add("foreign.asset", b"untouched")
        before = api.release["assets"][-1].copy()
        self.assertTrue(lic.ensure_license(api, "owner/repo", TAG, BIN, MIT_FIXTURE))
        self.assertIn(before, api.release["assets"])


if __name__ == "__main__":
    unittest.main()
