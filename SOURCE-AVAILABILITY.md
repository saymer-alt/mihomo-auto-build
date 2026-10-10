# MIPSel release source availability and redistribution review

**Status: practical source-location guide, NOT a compliance certification.**
Checked against GitHub Releases and upstream tagged LICENSE on 2026-10-10.
See [Issue #8](https://github.com/saymer-alt/mihomo-auto-build/issues/8) for open review items.

## How to obtain the source for the binary you downloaded

1. Find the **exact version** in the binary filename, e.g.
   `mihomo-linux-mipsel-softfloat-v1.19.32` → upstream `v1.19.32`.
2. Download its [tagged upstream source archive](https://github.com/MetaCubeX/mihomo/archive/refs/tags/v1.19.32.tar.gz)
   and inspect its [go.mod](https://github.com/MetaCubeX/mihomo/blob/v1.19.32/go.mod)
   / [go.sum](https://github.com/MetaCubeX/mihomo/blob/v1.19.32/go.sum).
   Use the **table below** for other versions. Do **not** use an unpinned upstream `main` branch.
3. Get source for the modules at the effective versions from the tagged
   `go.mod`/`go.sum` and any `replace` directives, e.g. via
   `go mod download -json all` in that tagged source tree; the
   [Go module proxy](https://proxy.golang.org/) can serve those exact module versions.
   `go version -m <binary>` reports build-info module versions from the
   released binary. **Both** build info and the tagged source should be cross-checked.
4. The build/packaging recipe (compiler target, flags, checksum creation, workflow)
   is in this repository: [build workflow](.github/workflows/build-mihomo-mipsel.yml),
   [asset publisher](scripts/release_assets.py) and
   [license collector](scripts/collect_upstream_licenses.py).
   See the release date and Git history to identify the **actual build commit**;
   current `main` may have changed since historic binaries were generated.
5. Verify the binary digest against the individual GitHub Release asset metadata.
   Only `v1.19.32` currently has a published `*.sha256` sidecar.
   A SHA-256 establishes integrity of bytes, **not** correspondence of
   all sources or the legal sufficiency of a source offer.

## Exact upstream version / source map

| Binary release | Download | Corresponding upstream source entry points | Archive note |
| --- | --- | --- | --- |
| `mipsel-v1.19.24` | [binary release](https://github.com/saymer-alt/mihomo-auto-build/releases/tag/mipsel-v1.19.24) | [tagged source](https://github.com/MetaCubeX/mihomo/tree/v1.19.24) · [source archive](https://github.com/MetaCubeX/mihomo/archive/refs/tags/v1.19.24.tar.gz) · [go.mod](https://github.com/MetaCubeX/mihomo/blob/v1.19.24/go.mod) · [go.sum](https://github.com/MetaCubeX/mihomo/blob/v1.19.24/go.sum) | Only binary observed; no SHA-256 or license notice assets |
| `mipsel-v1.19.25` | [binary release](https://github.com/saymer-alt/mihomo-auto-build/releases/tag/mipsel-v1.19.25) | [tagged source](https://github.com/MetaCubeX/mihomo/tree/v1.19.25) · [source archive](https://github.com/MetaCubeX/mihomo/archive/refs/tags/v1.19.25.tar.gz) · [go.mod](https://github.com/MetaCubeX/mihomo/blob/v1.19.25/go.mod) · [go.sum](https://github.com/MetaCubeX/mihomo/blob/v1.19.25/go.sum) | Only binary observed; no SHA-256 or license notice assets |
| `mipsel-v1.19.26` | [binary release](https://github.com/saymer-alt/mihomo-auto-build/releases/tag/mipsel-v1.19.26) | [tagged source](https://github.com/MetaCubeX/mihomo/tree/v1.19.26) · [source archive](https://github.com/MetaCubeX/mihomo/archive/refs/tags/v1.19.26.tar.gz) · [go.mod](https://github.com/MetaCubeX/mihomo/blob/v1.19.26/go.mod) · [go.sum](https://github.com/MetaCubeX/mihomo/blob/v1.19.26/go.sum) | Only binary observed; no SHA-256 or license notice assets |
| `mipsel-v1.19.27` | [binary release](https://github.com/saymer-alt/mihomo-auto-build/releases/tag/mipsel-v1.19.27) | [tagged source](https://github.com/MetaCubeX/mihomo/tree/v1.19.27) · [source archive](https://github.com/MetaCubeX/mihomo/archive/refs/tags/v1.19.27.tar.gz) · [go.mod](https://github.com/MetaCubeX/mihomo/blob/v1.19.27/go.mod) · [go.sum](https://github.com/MetaCubeX/mihomo/blob/v1.19.27/go.sum) | Only binary observed; no SHA-256 or license notice assets |
| `mipsel-v1.19.28` | [binary release](https://github.com/saymer-alt/mihomo-auto-build/releases/tag/mipsel-v1.19.28) | [tagged source](https://github.com/MetaCubeX/mihomo/tree/v1.19.28) · [source archive](https://github.com/MetaCubeX/mihomo/archive/refs/tags/v1.19.28.tar.gz) · [go.mod](https://github.com/MetaCubeX/mihomo/blob/v1.19.28/go.mod) · [go.sum](https://github.com/MetaCubeX/mihomo/blob/v1.19.28/go.sum) | Only binary observed; no SHA-256 or license notice assets |
| `mipsel-v1.19.29` | [binary release](https://github.com/saymer-alt/mihomo-auto-build/releases/tag/mipsel-v1.19.29) | [tagged source](https://github.com/MetaCubeX/mihomo/tree/v1.19.29) · [source archive](https://github.com/MetaCubeX/mihomo/archive/refs/tags/v1.19.29.tar.gz) · [go.mod](https://github.com/MetaCubeX/mihomo/blob/v1.19.29/go.mod) · [go.sum](https://github.com/MetaCubeX/mihomo/blob/v1.19.29/go.sum) | Only binary observed; no SHA-256 or license notice assets |
| `mipsel-v1.19.30` | [binary release](https://github.com/saymer-alt/mihomo-auto-build/releases/tag/mipsel-v1.19.30) | [tagged source](https://github.com/MetaCubeX/mihomo/tree/v1.19.30) · [source archive](https://github.com/MetaCubeX/mihomo/archive/refs/tags/v1.19.30.tar.gz) · [go.mod](https://github.com/MetaCubeX/mihomo/blob/v1.19.30/go.mod) · [go.sum](https://github.com/MetaCubeX/mihomo/blob/v1.19.30/go.sum) | Only binary observed; no SHA-256 or license notice assets |
| `mipsel-v1.19.31` | [binary release](https://github.com/saymer-alt/mihomo-auto-build/releases/tag/mipsel-v1.19.31) | [tagged source](https://github.com/MetaCubeX/mihomo/tree/v1.19.31) · [source archive](https://github.com/MetaCubeX/mihomo/archive/refs/tags/v1.19.31.tar.gz) · [go.mod](https://github.com/MetaCubeX/mihomo/blob/v1.19.31/go.mod) · [go.sum](https://github.com/MetaCubeX/mihomo/blob/v1.19.31/go.sum) | Only binary observed; no SHA-256 or license notice assets |
| `mipsel-v1.19.32` | [binary release](https://github.com/saymer-alt/mihomo-auto-build/releases/tag/mipsel-v1.19.32) | [tagged source](https://github.com/MetaCubeX/mihomo/tree/v1.19.32) · [source archive](https://github.com/MetaCubeX/mihomo/archive/refs/tags/v1.19.32.tar.gz) · [go.mod](https://github.com/MetaCubeX/mihomo/blob/v1.19.32/go.mod) · [go.sum](https://github.com/MetaCubeX/mihomo/blob/v1.19.32/go.sum) | Binary, SHA-256, GPL LICENSE, dependency summary and full license notices verified |

## GPLv3 §6(d) review checklist

The [GNU GPLv3 text](https://www.gnu.org/licenses/gpl-3.0.html) requires
that when object code is offered over a designated network location,
equivalent access to its **Complete Corresponding Source** must be offered
at no additional charge. Sources may reside on another server if there are
clear instructions next to the object code and equivalent download access.
The [FSF FAQ](https://www.gnu.org/licenses/gpl-faq.en.html#SourceAndBinaryOnDifferentSites)
explains this specifically.

- [x] Exact upstream source tags for the nine historical published binaries are identified.
- [x] The latest `v1.19.32` release has GPL-3.0 and third-party license notice assets.
- [ ] **Complete Corresponding Source** of the actual MIPSel binary is independently verified:
      exact build script revision, module versions and replacements, generated files,
      any compiled/embedded assets, and modification/install/run scripts where applicable.
- [ ] Evidence that a version-correct source link is displayed **next to each published binary**
      on every individual GitHub Release page, for all historical versions.
- [ ] Source download availability, public access, matching tagged trees and
      continued accessibility are verified for every release.
- [ ] Applicable GPL/LGPL/MPL obligations (see [20 module indicators](COPYLEFT-REVIEW.md), including any conditions specific to
      static linking/relinking or file-level source disclosures) have been
      reviewed against **actually incorporated code**, not simply 112 build-info modules.
- [ ] Requirements for all historical releases' license and attribution notices are
      addressed in a safe, reviewed backfill with binary IDs/digests unchanged.

### Limitations and safety

- No legal conclusion is made about compatibility of the 20 copyleft
  indicators in `v1.19.32` or exact obligations of particular modules.
- Upstream source and the current workflow are publicly readable, but this
  document does **not** assert that a release tarball containing all source,
  all build scripts or an exact binary-rebuild proof has been published.
- The `v1.19.24`–`v1.19.31` releases predate notice automation.
  Do **not** overwrite or reissue their binaries, silently add assets, or
  mark their license obligations resolved without separate review.
- This page is supplemental: to satisfy GPLv3 §6(d) online distribution,
  the release pages themselves should give easy-to-find version-specific
  source directions, not require discovering a document buried in Git history.

## Future release verification

The [scheduled build workflow](.github/workflows/build-mihomo-mipsel.yml)
checks upstream once a day. As of this review the upstream latest version
is `v1.19.32`; there is **no later upstream release** on which to validate the
new-version path in production. Offline unit tests are not a substitute for
a real future release. Re-check the first new version's binary/checksum,
notices, source links and build provenance when it becomes available.
