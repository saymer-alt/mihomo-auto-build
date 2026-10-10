# Licensing and provenance

> This is a provenance note, **not** a license grant for the build system.
> As of 2026-10-10, the owner has not selected a repository-wide license for
> the locally maintained workflows, Python tooling, tests or documentation.

## Two different components

| Component | Origin | License / status |
| --- | --- | --- |
| Mihomo binaries published in [Releases](https://github.com/saymer-alt/mihomo-auto-build/releases) | Built by GitHub Actions from tagged source in [MetaCubeX/mihomo](https://github.com/MetaCubeX/mihomo), not independently developed here | **Mihomo upstream uses the MIT license**; see [upstream LICENSE](https://github.com/MetaCubeX/mihomo/blob/main/LICENSE) and the exact source tag used for each binary. Relevant third-party dependency notices may also apply. |
| `.github/workflows/`, `scripts/`, `tests/`, this repository's README | The local builder, packaging and tests | **No explicit repository-wide license selected yet.** The upstream Mihomo license does not automatically license this build/automation code. |

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

## Next owner decisions

1. Verify provenance/originality of the build scripts, workflow and tests.
2. Decide whether to license **only those local files** under a software
   license such as MIT (one possible option, **not** already chosen).
3. Add a scoped `LICENSE` or per-directory licensing notices **only after**
   the owner chooses the grant and author/title attribution is verified.
4. Add a tested release notice artifact or another demonstrably compliant
   way of delivering upstream licenses with each binary.
5. Consider a historical-asset cleanup plan only if a review confirms it is
   needed; never silently replace working released binaries.

For ordinary build bugs use [Issues](https://github.com/saymer-alt/mihomo-auto-build/issues).
For undisclosed security vulnerabilities, follow [SECURITY.md](SECURITY.md).
