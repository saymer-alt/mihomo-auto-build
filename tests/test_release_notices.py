# SPDX-License-Identifier: MIT
"""Offline verification of third-party notice publication and fail-closed guards."""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest

import release_notices as notices
from test_release_assets import BIN, Fake, TAG

ME = notices.assets.MetadataError

VER = TAG.removeprefix("mipsel-")  # v1.19.32
SUMMARY_NAME = f"THIRD_PARTY_LICENSES-{VER}.txt"
FULL_NAME = f"THIRD_PARTY_NOTICES-{VER}.txt"
SUMMARY = (f"Third-party license summary for Mihomo {VER} (MIPSel rebuild).\n"
           .encode() + b"row | MIT | LICENSE | (c) someone\n" * 20)
FULL = b"THIRD-PARTY SOFTWARE NOTICES for Mihomo " + VER.encode() + b"\n" + b"text\n" * 100


class NoticeTests(unittest.TestCase):
    def publish(self, api, summary=SUMMARY, full=FULL):
        with tempfile.TemporaryDirectory() as directory:
            s = Path(directory, SUMMARY_NAME)
            f = Path(directory, FULL_NAME)
            s.write_bytes(summary)
            f.write_bytes(full)
            return notices.publish(api, "owner/repo", TAG, {SUMMARY_NAME: s, FULL_NAME: f})

    def test_missing_assets_upload_and_rerun_is_noop(self):
        api = Fake(side=True)
        originals = list(api.release["assets"])
        uploaded = self.publish(api)
        self.assertEqual(uploaded, [SUMMARY_NAME, FULL_NAME])
        names = [a["name"] for a in api.release["assets"]]
        self.assertIn(SUMMARY_NAME, names)
        self.assertIn(FULL_NAME, names)
        self.assertEqual(api.release["assets"][:len(originals)], originals)
        before = list(api.release["assets"])
        self.assertEqual(self.publish(api), [])
        self.assertEqual(before, api.release["assets"])
        self.assertFalse(any(method == "DELETE" for method, _ in api.calls))

    def test_existing_matching_asset_not_replaced(self):
        api = Fake(side=True)
        api.add(SUMMARY_NAME, SUMMARY)
        original = copy.deepcopy(api.release["assets"][-1])
        uploaded = self.publish(api)
        self.assertEqual(uploaded, [FULL_NAME])
        self.assertEqual(api.release["assets"][-2], original)

    def test_conflicting_or_corrupt_existing_asset_fails_closed(self):
        for mutation in ("bytes", "digest", "size", "duplicate", "starter"):
            api = Fake(side=True)
            api.add(SUMMARY_NAME, SUMMARY)
            asset = api.release["assets"][-1]
            if mutation == "bytes":
                api.content[asset["id"]] = SUMMARY + b"tampered"
            elif mutation == "digest":
                asset["digest"] = "sha256:" + "0" * 64
            elif mutation == "size":
                asset["size"] = asset["size"] + 1
            elif mutation == "duplicate":
                api.release["assets"].append(dict(asset, id=asset["id"] + 1))
            else:
                asset.update(size=0, state="starter", digest=None)
            before = copy.deepcopy(api.release["assets"])
            with self.assertRaises(ME):
                self.publish(api)
            self.assertEqual(api.release["assets"], before)
            self.assertFalse(any(x[0] in ("UPLOAD", "DELETE") for x in api.calls))

    def test_existing_conflicting_second_notice_aborts_before_first_upload(self):
        # If summary is missing but full notices exist and differ, fail
        # before uploading the summary (no avoidable partial release).
        api = Fake(side=True)
        api.add(FULL_NAME, b"incorrect full notice")
        original = copy.deepcopy(api.release["assets"])
        with self.assertRaises(ME):
            self.publish(api)
        self.assertEqual(api.release["assets"], original)
        self.assertFalse(any(method in ("UPLOAD", "DELETE") for method, _ in api.calls))

    def test_upload_failure_preserves_release_then_retries(self):
        api = Fake(side=True)
        originals = copy.deepcopy(api.release["assets"])
        api.fail_upload = True
        with self.assertRaises(Exception):
            self.publish(api)
        self.assertEqual(api.release["assets"], originals)
        api.fail_upload = False
        self.assertEqual(self.publish(api), [SUMMARY_NAME, FULL_NAME])

    def test_concurrent_notice_upload_conflict_then_idempotent(self):
        api = Fake(side=True)
        originals = copy.deepcopy(api.release["assets"])
        real_upload = api.upload

        def upload(tag, path):
            # A concurrent actor attaches the same-named full notices first.
            if path.name == SUMMARY_NAME:
                api.content[999] = SUMMARY
                api.release["assets"].append(
                    {"id": 999, "name": path.name, "state": "uploaded",
                     "size": len(SUMMARY),
                     "digest": "sha256:" + hashlib.sha256(SUMMARY).hexdigest()})
            real_upload(tag, path)

        api.upload = upload
        with self.assertRaises((ME, Exception)):
            self.publish(api)
        # Rerun: the concurrent summary matches, the full notices are added.
        uploaded = self.publish(api)
        self.assertEqual(uploaded, [FULL_NAME])
        self.assertEqual(len(api.release["assets"]), len(originals) + 2)

    def test_foreign_assets_untouched_and_binaries_protected(self):
        api = Fake(side=True)
        api.add("foreign.asset", b"untouched")
        before = copy.deepcopy(api.release["assets"])
        self.publish(api)
        for asset in before:
            self.assertIn(asset, api.release["assets"])

    def test_wrong_version_pairing_refused(self):
        api = Fake(side=True)
        with tempfile.TemporaryDirectory() as directory:
            s = Path(directory, "THIRD_PARTY_LICENSES-v9.9.9.txt")
            s.write_bytes(SUMMARY)
            with self.assertRaises(ME):
                notices.publish(api, "owner/repo", TAG,
                                {"THIRD_PARTY_LICENSES-v9.9.9.txt": s,
                                 FULL_NAME: Path(directory, FULL_NAME)})
        self.assertFalse(any(x[0] == "UPLOAD" for x in api.calls))

    def test_missing_or_binary_local_file_refused(self):
        api = Fake(side=True)
        with tempfile.TemporaryDirectory() as directory:
            empty = Path(directory, SUMMARY_NAME)
            empty.write_bytes(b"")
            with self.assertRaisesRegex(ME, "missing or empty"):
                self.publish(api, summary=b"")
        self.assertFalse(any(x[0] == "UPLOAD" for x in api.calls))

    def test_approved_legacy_gplv2_notice_is_verified_without_mutation(self):
        module = notices.GOLZO
        old_summary = (
            module + " | LGPL-2.1 | LICENSE.gpl | -\n"
            + "  " + module + " -> LGPL-2.1\n").encode()
        fixed_summary = old_summary.decode().replace("LGPL-2.1", "GPL-2.0").encode()
        old_full = (
            "--- " + module + " | license: LGPL-2.1 | files: LICENSE.gpl\n"
            + "GNU GENERAL PUBLIC LICENSE\nVersion 2, June 1991\n").encode()
        fixed_full = old_full.replace(b"license: LGPL-2.1", b"license: GPL-2.0")
        api = Fake(side=True)
        api.add(SUMMARY_NAME, old_summary)
        api.add(FULL_NAME, old_full)
        summary_digest = "sha256:" + hashlib.sha256(old_summary).hexdigest()
        api.release["body"] = (
            notices.ERRATA_MARKER
            + "\nCorrection: " + module + ", GPL version 2\n"
            + "Original summary digest: " + summary_digest + "\n")
        before = copy.deepcopy(api.release["assets"])
        s = notices.verify_asset_with_audited_erratum(
            api, "owner/repo", api.release, SUMMARY_NAME, fixed_summary)
        f = notices.verify_asset_with_audited_erratum(
            api, "owner/repo", api.release, FULL_NAME, fixed_full)
        self.assertIsNotNone(s)
        self.assertIsNotNone(f)
        self.assertEqual(api.release["assets"], before)
        self.assertFalse(any(action in ("UPLOAD", "DELETE") for action, _ in api.calls))

    def test_legacy_notice_refuses_missing_erratum_and_other_drift(self):
        module = notices.GOLZO
        old_summary = (
            module + " | LGPL-2.1 | LICENSE.gpl | -\n"
            + "  " + module + " -> LGPL-2.1\n").encode()
        fixed = old_summary.replace(b"LGPL-2.1", b"GPL-2.0")
        api = Fake(side=True)
        api.add(SUMMARY_NAME, old_summary)
        digest = "sha256:" + hashlib.sha256(old_summary).hexdigest()
        api.release["body"] = ""
        with self.assertRaises(ME):
            notices.verify_asset_with_audited_erratum(
                api, "owner/repo", api.release, SUMMARY_NAME, fixed)
        api.release["body"] = (
            notices.ERRATA_MARKER + "\n" + module + ", GPL version 2\n"
            + "Original summary digest: " + digest + "\n")
        with self.assertRaises(ME):
            notices.verify_asset_with_audited_erratum(
                api, "owner/repo", api.release, SUMMARY_NAME,
                fixed + b"unexpected additional drift")
        api.release["body"] = api.release["body"].replace(digest, "sha256:" + "0"*64)
        with self.assertRaises(ME):
            notices.verify_asset_with_audited_erratum(
                api, "owner/repo", api.release, SUMMARY_NAME, fixed)

    def test_expected_names_derived_from_tag(self):
        self.assertEqual(notices.expected_names(TAG),
                         ("THIRD_PARTY_LICENSES-v1.19.32.txt",
                          "THIRD_PARTY_NOTICES-v1.19.32.txt"))
        with self.assertRaises(ME):
            notices.expected_names("mipsel-v1.19.32/../../etc")


if __name__ == "__main__":
    unittest.main()
