# Licensing and provenance

> **Owner decision (2026-10-10):** the original build automation, tests and
> accompanying project documentation written by `saymer-alt` are distributed
> under the **MIT License** ([LICENSE](LICENSE)).
> This grant does not relicense upstream Mihomo, third-party code, dependencies,
> or existing released binary assets.

## Two different components

| Component | Origin | License / status |
| --- | --- | --- |
| Mihomo binaries published in [Releases](https://github.com/saymer-alt/mihomo-auto-build/releases) | Built by GitHub Actions from tagged source in [MetaCubeX/mihomo](https://github.com/MetaCubeX/mihomo), not independently developed here | **Mihomo upstream is licensed under GNU GPL version 3**; verified on 2026-10-10 against the LICENSE file of every tag used for published binaries (`v1.19.24`…`v1.19.32`) and of `main`. See [upstream LICENSE](https://github.com/MetaCubeX/mihomo/blob/v1.19.32/LICENSE) for the exact tagged text and [UPSTREAM_NOTICE.md](UPSTREAM_NOTICE.md) for the reproduced copy. Third-party dependency notices may also apply. |
| `.github/workflows/build-mihomo-mipsel.yml`, `.github/workflows/test-release-readiness.yml`, `scripts/release_assets.py`, `scripts/release_license.py`, `scripts/collect_upstream_licenses.py`, `scripts/release_notices.py`, `tests/test_*.py` | Original local builder, publishing logic and tests | **MIT**, Copyright (c) 2026 saymer-alt — [LICENSE](LICENSE). |
| Original project-specific README, CONTRIBUTING and SECURITY text | Maintainer-written documentation | **MIT** where owned by saymer-alt. Third-party quotations retain their own terms. |

See [UPSTREAM_NOTICE.md](UPSTREAM_NOTICE.md) for the upstream Mihomo GPL-3.0
license text as reproduced from the upstream repository. It applies **to the
upstream Mihomo component**, not to the original builder code in this
repository.

## Upstream GPL-3.0 and redistribution

GPL-3.0 imposes more obligations than the MIT notice previously assumed:
anyone who conveys a published binary must pass along the license text,
carry applicable copyright notices, and offer the **complete corresponding
source**. Tagged upstream sources and this repository's version-appropriate
build scripts are **starting points**, but the required source may also
include dependency modules, generated/embedded data and applicable installation
or modification scripts. The completeness of the actual published binaries'
source has **not** been established. See [SOURCE-AVAILABILITY.md](SOURCE-AVAILABILITY.md)
for exact source entry points and the GPLv3 §6(d) checklist. `scripts/release_license.py` now validates
and attaches the exact tagged GPL-3.0 text as `<binary>.LICENSE`;
`scripts/collect_upstream_licenses.py` produces the dependency notice
summary and full texts. This does not change the license of anything the
owner owns; it corrects the factual record about upstream.

> Earlier versions of this file and of `UPSTREAM_NOTICE.md` (before
> 2026-10-10, later the same day) described upstream as "MIT, Copyright
> 2023 KT". That description was incorrect for every tag used by published
> releases; it was corrected in the PR #12 review cycle.

## Release-distribution follow-up (technical inventory, 2026-10-11)

All **nine** published MIPSel releases (`v1.19.24`–`v1.19.32`) now contain
five downloadable assets each: the original binary, SHA-256 sidecar,
tagged upstream GPL-3.0 LICENSE, module-license summary and full notice texts.
The 2026-10-10 owner-approved backfill added four missing assets to each of
eight historical releases; existing binary IDs, sizes and digests were preserved.
Evidence: [Issue #8 verified backfill report](https://github.com/saymer-alt/mihomo-auto-build/issues/8#issuecomment-6102988561).

**Open gaps confirmed 2026-10-11:**
- All nine Release descriptions now include version-pinned upstream
  source pointers ([PR #23](https://github.com/saymer-alt/mihomo-auto-build/pull/23)).
  The precise historic builder revisions and full corresponding source
  still require verification; source pointers alone do not prove compliance.
- Seven original historical `THIRD_PARTY_LICENSES` summaries
  (v1.19.26–v1.19.32) **incorrectly identify `rasky/go-lzo` as
  LGPL-2.1**; pinned upstream sources identify it as GPLv2. The
  original files remain unchanged; all seven Release descriptions
  now carry a prominent correction. The classifier and precisely
  scoped immutable legacy verifier were fixed in
  [PR #21](https://github.com/saymer-alt/mihomo-auto-build/pull/21).
  A [cross-compiled package graph check](https://github.com/saymer-alt/mihomo-auto-build/actions/runs/38131113277)
  confirms go-lzo imports for v1.19.32. Exact linked-symbol inclusion and
  license compatibility remain open.
- Presence of notices is not proof of license compatibility, actual module
  linkage or Complete Corresponding Source availability.

**Do not overwrite or delete existing release assets** to repair notice
metadata. A correction must be reviewable and must preserve immutable
binary evidence, with any existing notice discrepancies disclosed.

The workflow retrieves the exact source-tag `LICENSE`, safely publishes
`<binary>.LICENSE` alongside the already verified binary and SHA-256
sidecar, and — after the third-party notice files for that version have
been generated and reviewed — attaches `THIRD_PARTY_LICENSES-<version>.txt`
and `THIRD_PARTY_NOTICES-<version>.txt`. If an existing notice differs, or
an upload is incomplete, every step refuses mutation and reports an error.
This is **not** a completed legal review: the [20 GPL/LGPL/MPL indicators](COPYLEFT-REVIEW.md)
require human provenance and actual-linkage review tracked in
[Issue #8](https://github.com/saymer-alt/mihomo-auto-build/issues/8).

## License boundaries and remaining work

- The owner chose MIT for original local automation and documentation on
  2026-10-10. [LICENSE](LICENSE) is the operative grant for that code.
  The upstream Mihomo GPL-3.0 license is distinct; neither grant
  supersedes the other, and no license change is proposed for either.
- New external contributions require independent rights/provenance review;
  the owner cannot relicense another person's work without permission.
- **Third-party Go module incorporation**, correct license identity (including
  the `rasky/go-lzo` GPLv2 finding), and Complete Corresponding Source
  still require review in [Issue #8](https://github.com/saymer-alt/mihomo-auto-build/issues/8).
- Original checksum and notice assets for all historical releases have been
  added and verified. Future corrections require separate review; never
  overwrite working binaries or silently rewrite released assets.

For ordinary build bugs use [Issues](https://github.com/saymer-alt/mihomo-auto-build/issues).
For undisclosed security vulnerabilities, follow [SECURITY.md](SECURITY.md).
