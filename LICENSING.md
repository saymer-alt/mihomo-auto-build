# Licensing and provenance

> **Owner decision (2026-10-10):** the original build automation, tests and
> accompanying project documentation written by `saymer-alt` are distributed
> under the **MIT License** ([LICENSE](LICENSE)).
> This grant does not relicense upstream Mihomo, third-party code, dependencies,
> or existing released binary assets.

## Two different components

| Component | Origin | License / status |
| --- | --- | --- |
| Mihomo binaries published in [Releases](https://github.com/saymer-alt/mihomo-auto-build/releases) | Built by GitHub Actions from tagged source in [MetaCubeX/mihomo](https://github.com/MetaCubeX/mihomo), not independently developed here | **Mihomo upstream uses the MIT license**; see [upstream LICENSE](https://github.com/MetaCubeX/mihomo/blob/main/LICENSE) and the exact source tag used for each binary. Relevant third-party dependency notices may also apply. |
| `.github/workflows/build-mihomo-mipsel.yml`, `.github/workflows/test-release-readiness.yml`, `scripts/release_assets.py`, `tests/test_release_assets.py`, `tests/test_starter_recovery.py` | Original local builder, publishing logic and tests | **MIT**, Copyright (c) 2026 saymer-alt — [LICENSE](LICENSE). |
| Original project-specific README, CONTRIBUTING and SECURITY text | Maintainer-written documentation | **MIT** where owned by saymer-alt. Third-party quotations retain their own terms. |

See [UPSTREAM_NOTICE.md](UPSTREAM_NOTICE.md) for the upstream Mihomo MIT
copyright and permission notice as checked in the upstream repository.
This notice applies **to the upstream Mihomo component**, not automatically to
the original builder code in this repository.

## Release-distribution follow-up

As inspected on 2026-10-10:

- Release `mipsel-v1.19.32` includes the binary and SHA-256 sidecar.
- Earlier releases `mipsel-v1.19.31` and `mipsel-v1.19.30` were observed to
  have only the binary asset.
- An independently downloadable upstream `LICENSE` or `NOTICE` asset was
  **not** present in these inspected releases.

The upstream MIT license requires preserving its copyright and permission
notice in copies/substantial portions. A future workflow change should ensure
that each redistributed upstream binary is accompanied by the applicable
license notice(s), not only a checksum. The exact packaging and dependency
attribution scheme need a separate implementation, tests and review; this
document alone does not prove past release compliance.

## License boundaries and remaining work

- The owner chose MIT for original local automation and documentation on
  2026-10-10. [LICENSE](LICENSE) is the operative grant for that code.
  The upstream Mihomo MIT notice is distinct, with its own
  `Copyright 2023 KT`; neither notice supersedes the other.
- New external contributions require independent rights/provenance review;
  the owner cannot relicense another person's work without permission.
- Shipping the license/required third-party notices **with each released
  binary** remains a separate task in
  [Issue #8](https://github.com/saymer-alt/mihomo-auto-build/issues/8).
- Consider historical release updates only after separate review. Never
  overwrite working binaries or silently rewrite released assets.

For ordinary build bugs use [Issues](https://github.com/saymer-alt/mihomo-auto-build/issues).
For undisclosed security vulnerabilities, follow [SECURITY.md](SECURITY.md).
