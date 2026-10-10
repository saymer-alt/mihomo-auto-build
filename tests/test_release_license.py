# SPDX-License-Identifier: MIT
"""Offline verification of upstream license publication and fail-closed guards."""
import hashlib
import io
import os
import subprocess
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import release_license as lic
from test_release_assets import BIN, TAG, DATA, Fake, m


# Canonical FSF GPL-3.0 markers; the real tagged file is ~35 KB.
GPL3_FIXTURE = (b"                    GNU GENERAL PUBLIC LICENSE\n"
                b"                       Version 3, 29 June 2007\n"
                b" Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>\n"
                + b"license notice text\n" * 15)


class LicenseTests(unittest.TestCase):
    def test_upload_then_rerun_preserves_binary_and_checksum(self):
        api = Fake(side=True)
        originals = list(api.release["assets"])
        self.assertTrue(lic.ensure_license(api, "owner/repo", TAG, BIN, GPL3_FIXTURE))
        self.assertEqual(api.release["assets"][:2], originals)
        self.assertEqual(lic.license_name(BIN), BIN + ".LICENSE")
        before = list(api.release["assets"])
        self.assertFalse(lic.ensure_license(api, "owner/repo", TAG, BIN, GPL3_FIXTURE))
        self.assertEqual(before, api.release["assets"])
        self.assertFalse(any(method == "DELETE" for method, _ in api.calls))
        self.assertNotIn(("UPLOAD", BIN), api.calls)
        self.assertNotIn(("UPLOAD", BIN + ".sha256"), api.calls)

    def test_checksum_missing_or_binary_missing_refuses_notice(self):
        for api in (Fake(), Fake(binary=None)):
            with self.assertRaisesRegex(lic.assets.MetadataError, "must be complete"):
                lic.ensure_license(api, "owner/repo", TAG, BIN, GPL3_FIXTURE)
            self.assertFalse(any(x[0] in ("UPLOAD", "DELETE") for x in api.calls))

    def test_invalid_or_conflicting_notice_fails_closed(self):
        for bytes_ in (b"different", b"", GPL3_FIXTURE + b"bad"):
            api = Fake(side=True)
            api.add(BIN + ".LICENSE", bytes_)
            before = list(api.release["assets"])
            with self.assertRaises(lic.assets.MetadataError):
                lic.ensure_license(api, "owner/repo", TAG, BIN, GPL3_FIXTURE)
            self.assertEqual(before, api.release["assets"])
            self.assertFalse(any(x[0] in ("UPLOAD", "DELETE") for x in api.calls))

    def test_duplicate_and_starter_notice_refused(self):
        for make in ("duplicate", "starter"):
            api = Fake(side=True)
            api.add(BIN + ".LICENSE", GPL3_FIXTURE)
            if make == "duplicate":
                api.release["assets"].append(dict(api.release["assets"][-1], id=777))
            else:
                api.release["assets"][-1].update(size=0, state="starter", digest=None)
            with self.assertRaises(lic.assets.MetadataError):
                lic.ensure_license(api, "owner/repo", TAG, BIN, GPL3_FIXTURE)
            self.assertFalse(any(x[0] in ("UPLOAD", "DELETE") for x in api.calls))

    def test_failed_upload_retry_preserves_existing_assets(self):
        api = Fake(side=True)
        original = list(api.release["assets"])
        api.fail_upload = True
        with self.assertRaises(Exception):
            lic.ensure_license(api, "owner/repo", TAG, BIN, GPL3_FIXTURE)
        self.assertEqual(api.release["assets"], original)
        api.fail_upload = False
        self.assertTrue(lic.ensure_license(api, "owner/repo", TAG, BIN, GPL3_FIXTURE))

    def test_invalid_tag_or_license_refused_before_mutation(self):
        api = Fake(side=True)
        for wrongtag, wrongbin, notice in (
            (TAG, BIN + "-another", GPL3_FIXTURE),
            ("mipsel-v1.19.32/../../main", BIN, GPL3_FIXTURE),
            (TAG, BIN, b"not upstream"),
        ):
            with self.assertRaises(lic.assets.MetadataError):
                lic.ensure_license(api, "owner/repo", wrongtag, wrongbin, notice)
        self.assertFalse(any(x[0] in ("UPLOAD", "DELETE") for x in api.calls))

    def test_license_fetched_from_exact_upstream_tag(self):
        with patch.object(lic, "urlopen", return_value=io.BytesIO(GPL3_FIXTURE)) as mocked:
            self.assertEqual(lic.download_tagged_license(TAG), GPL3_FIXTURE)
            self.assertEqual(mocked.call_args.args[0],
                             "https://raw.githubusercontent.com/MetaCubeX/mihomo/v1.19.32/LICENSE")
        with self.assertRaises(lic.assets.MetadataError):
            lic.download_tagged_license("mipsel-v1.19.32/../../main")

    def test_foreign_release_assets_unchanged(self):
        api = Fake(side=True)
        api.add("foreign.asset", b"untouched")
        before = api.release["assets"][-1].copy()
        self.assertTrue(lic.ensure_license(api, "owner/repo", TAG, BIN, GPL3_FIXTURE))
        self.assertIn(before, api.release["assets"])


class LicenseEdgeCases(unittest.TestCase):
    def test_cli_exception_handler_handles_missing_arguments(self):
        # Invokes __main__: importing subprocess only inside main() would
        # cause NameError while resolving the except tuple on this path.
        script = Path(__file__).resolve().parents[1] / "scripts" / "release_license.py"
        result = subprocess.run([sys.executable, str(script)],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("Expected release tag and binary name", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_oversized_upstream_license_refused(self):
        oversized = GPL3_FIXTURE + b"x" * lic.LICENSE_MAX_BYTES
        with self.assertRaisesRegex(lic.assets.MetadataError, "length"):
            lic.validate_license(oversized)
        # The real canonical GPL-3.0 text (~35 KB) stays inside the 64 KB cap.
        real = Path(__file__).resolve().parents[1] / "UPSTREAM_NOTICE.md"
        text = real.read_text(encoding="utf-8").split("---", 1)[1].strip().encode()
        self.assertEqual(lic.validate_license(text), text)

    def test_non_utf8_upstream_license_refused(self):
        with self.assertRaisesRegex(lic.assets.MetadataError, "UTF-8"):
            lic.validate_license(GPL3_FIXTURE.rstrip(b"\n") + b"\xff")

    def test_notice_asset_without_digest_fails_closed(self):
        api = Fake(side=True)
        api.add(BIN + ".LICENSE", GPL3_FIXTURE)
        api.release["assets"][-1].pop("digest")
        before = list(api.release["assets"])
        with self.assertRaisesRegex(lic.assets.MetadataError, "digest"):
            lic.ensure_license(api, "owner/repo", TAG, BIN, GPL3_FIXTURE)
        self.assertEqual(before, api.release["assets"])

    def test_concurrent_notice_during_upload_conflicts_then_idempotent(self):
        api = Fake(side=True)
        original = list(api.release["assets"])

        def upload(tag, path):
            # Another actor attaches the same-named notice right before ours.
            api.content[999] = GPL3_FIXTURE
            api.release["assets"].append({"id": 999, "name": path.name, "state": "uploaded",
                                          "size": len(GPL3_FIXTURE),
                                          "digest": "sha256:" + hashlib.sha256(GPL3_FIXTURE).hexdigest()})
            # Real gh release upload without --clobber fails the same way.
            api.calls.append(("UPLOAD", path.name))
            raise m.MetadataError("conflict")

        api.upload = upload
        with self.assertRaises((m.MetadataError, lic.assets.MetadataError)):
            lic.ensure_license(api, "owner/repo", TAG, BIN, GPL3_FIXTURE)
        # The concurrent notice is identical to the tagged upstream, so a rerun
        # verifies it instead of mutating anything.
        self.assertFalse(lic.ensure_license(api, "owner/repo", TAG, BIN, GPL3_FIXTURE))
        self.assertEqual(len(api.release["assets"]), len(original) + 1)

    def test_upload_with_corrupted_result_is_refused(self):
        api = Fake(side=True)
        before = list(api.release["assets"])

        def upload(tag, path):
            # Simulate server-side mangling: asset lands but bytes differ.
            api.content[999] = GPL3_FIXTURE + b"x"
            api.release["assets"].append({"id": 999, "name": path.name, "state": "uploaded",
                                          "size": len(GPL3_FIXTURE) + 1,
                                          "digest": "sha256:" + hashlib.sha256(GPL3_FIXTURE + b"x").hexdigest()})

        api.upload = upload
        with self.assertRaisesRegex(lic.assets.MetadataError,
                                    "does not match tagged upstream"):
            lic.ensure_license(api, "owner/repo", TAG, BIN, GPL3_FIXTURE)
        self.assertEqual([a for a in api.release["assets"] if a["name"] != BIN + ".LICENSE"],
                         before)

    def test_missing_environment_refuses_cleanly(self):
        # GITHUB_REPOSITORY absent -> clean MetadataError (mapped to exit 2 by
        # the module's error handler) instead of a KeyError traceback.
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(sys, "argv", ["release_license.py", TAG, BIN]):
                with patch.object(lic, "download_tagged_license", return_value=GPL3_FIXTURE):
                    with self.assertRaises(lic.assets.MetadataError):
                        lic.main()


if __name__ == "__main__":
    unittest.main()
