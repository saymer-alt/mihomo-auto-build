# SPDX-License-Identifier: MIT
"""Offline checks for immutable source pointers on newly created releases."""
import unittest

from test_release_assets import m


class SourceAvailabilityTests(unittest.TestCase):
    def test_release_links_are_tagged_and_builder_ref_immutable(self):
        sha = "a" * 40
        content = m.release_body("mipsel-v1.19.32", "saymer-alt/mihomo-auto-build", sha)
        self.assertIn("https://github.com/MetaCubeX/mihomo/archive/refs/tags/v1.19.32.tar.gz", content)
        self.assertIn(f"https://github.com/saymer-alt/mihomo-auto-build/archive/{sha}.zip", content)
        self.assertIn(f"/blob/{sha}/.github/workflows/build-mihomo-mipsel.yml", content)
        self.assertIn(f"/blob/{sha}/SOURCE-AVAILABILITY.md", content)
        self.assertIn("go.mod", content)
        self.assertIn("replace directives", content)
        self.assertIn("GPLv3", content)
        self.assertNotIn("/tree/main", content)
        self.assertNotIn("/blob/main", content)
        self.assertIn("\n\n## Corresponding source", content)
        self.assertNotIn("\\n", content)

    def test_rejects_untrusted_tags_repo_and_unpinned_builder(self):
        for tag, repo, sha in (
            ("mipsel-v1.19.32/../main", "saymer-alt/mihomo-auto-build", "a" * 40),
            ("mipsel-v1.19.32", "bad/repo/nested", "a" * 40),
            ("mipsel-v1.19.32", "saymer-alt/mihomo-auto-build", ""),
            ("mipsel-v1.19.32", "saymer-alt/mihomo-auto-build", "main"),
            ("mipsel-v1.19.32", "saymer-alt/mihomo-auto-build", "b" * 39),
        ):
            with self.subTest(tag=tag, repo=repo, sha=sha):
                with self.assertRaises(m.MetadataError):
                    m.release_body(tag, repo, sha)


if __name__ == "__main__":
    unittest.main()
