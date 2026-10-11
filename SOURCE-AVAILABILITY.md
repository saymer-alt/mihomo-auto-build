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
   Consult the [historical build-provenance map](docs/HISTORICAL-BUILD-PROVENANCE-2026-10-11.md)
   for all nine GitHub Actions run head SHAs, pinned builder workflow revisions
   and actual Go compiler versions. For the five oldest releases the Go
   version was recovered directly from SHA-256-verified original binary
   build-info in [successful read-only CI](https://github.com/saymer-alt/mihomo-auto-build/actions/runs/38132608435),
   while the old Actions run logs expired. Their build-to-release association
   is still not an independently proven binary attestation. Do **not** substitute
   current `main` for a historical build revision.
5. Verify the binary digest against the individual GitHub Release asset metadata.
   All nine published versions (`v1.19.24`–`v1.19.32`) have a `*.sha256` sidecar and GPL/dependency notices after the verified 2026-10-10 backfill.
   A SHA-256 establishes integrity of bytes, **not** correspondence of
   all sources or the legal sufficiency of a source offer.

The [nine-release historical Actions map](docs/HISTORICAL-BUILD-PROVENANCE-2026-10-11.md)
records the original builder source snapshot candidates alongside exact
tagged upstream source commits. This narrows—but does not close—the
Complete Corresponding Source and reproducibility review.

## Exact upstream version / source map

| Binary release | Download | Corresponding upstream source entry points | Archive note |
| --- | --- | --- | --- |
| `mipsel-v1.19.24` | [binary release](https://github.com/saymer-alt/mihomo-auto-build/releases/tag/mipsel-v1.19.24) | [tagged source](https://github.com/MetaCubeX/mihomo/tree/v1.19.24) · [source archive](https://github.com/MetaCubeX/mihomo/archive/refs/tags/v1.19.24.tar.gz) · [go.mod](https://github.com/MetaCubeX/mihomo/blob/v1.19.24/go.mod) · [go.sum](https://github.com/MetaCubeX/mihomo/blob/v1.19.24/go.sum) | 2026-10-10 backfill: five assets verified; original binary unchanged |
| `mipsel-v1.19.25` | [binary release](https://github.com/saymer-alt/mihomo-auto-build/releases/tag/mipsel-v1.19.25) | [tagged source](https://github.com/MetaCubeX/mihomo/tree/v1.19.25) · [source archive](https://github.com/MetaCubeX/mihomo/archive/refs/tags/v1.19.25.tar.gz) · [go.mod](https://github.com/MetaCubeX/mihomo/blob/v1.19.25/go.mod) · [go.sum](https://github.com/MetaCubeX/mihomo/blob/v1.19.25/go.sum) | 2026-10-10 backfill: five assets verified; original binary unchanged |
| `mipsel-v1.19.26` | [binary release](https://github.com/saymer-alt/mihomo-auto-build/releases/tag/mipsel-v1.19.26) | [tagged source](https://github.com/MetaCubeX/mihomo/tree/v1.19.26) · [source archive](https://github.com/MetaCubeX/mihomo/archive/refs/tags/v1.19.26.tar.gz) · [go.mod](https://github.com/MetaCubeX/mihomo/blob/v1.19.26/go.mod) · [go.sum](https://github.com/MetaCubeX/mihomo/blob/v1.19.26/go.sum) | 2026-10-10 backfill: five assets verified; original binary unchanged |
| `mipsel-v1.19.27` | [binary release](https://github.com/saymer-alt/mihomo-auto-build/releases/tag/mipsel-v1.19.27) | [tagged source](https://github.com/MetaCubeX/mihomo/tree/v1.19.27) · [source archive](https://github.com/MetaCubeX/mihomo/archive/refs/tags/v1.19.27.tar.gz) · [go.mod](https://github.com/MetaCubeX/mihomo/blob/v1.19.27/go.mod) · [go.sum](https://github.com/MetaCubeX/mihomo/blob/v1.19.27/go.sum) | 2026-10-10 backfill: five assets verified; original binary unchanged |
| `mipsel-v1.19.28` | [binary release](https://github.com/saymer-alt/mihomo-auto-build/releases/tag/mipsel-v1.19.28) | [tagged source](https://github.com/MetaCubeX/mihomo/tree/v1.19.28) · [source archive](https://github.com/MetaCubeX/mihomo/archive/refs/tags/v1.19.28.tar.gz) · [go.mod](https://github.com/MetaCubeX/mihomo/blob/v1.19.28/go.mod) · [go.sum](https://github.com/MetaCubeX/mihomo/blob/v1.19.28/go.sum) | 2026-10-10 backfill: five assets verified; original binary unchanged |
| `mipsel-v1.19.29` | [binary release](https://github.com/saymer-alt/mihomo-auto-build/releases/tag/mipsel-v1.19.29) | [tagged source](https://github.com/MetaCubeX/mihomo/tree/v1.19.29) · [source archive](https://github.com/MetaCubeX/mihomo/archive/refs/tags/v1.19.29.tar.gz) · [go.mod](https://github.com/MetaCubeX/mihomo/blob/v1.19.29/go.mod) · [go.sum](https://github.com/MetaCubeX/mihomo/blob/v1.19.29/go.sum) | 2026-10-10 backfill: five assets verified; original binary unchanged |
| `mipsel-v1.19.30` | [binary release](https://github.com/saymer-alt/mihomo-auto-build/releases/tag/mipsel-v1.19.30) | [tagged source](https://github.com/MetaCubeX/mihomo/tree/v1.19.30) · [source archive](https://github.com/MetaCubeX/mihomo/archive/refs/tags/v1.19.30.tar.gz) · [go.mod](https://github.com/MetaCubeX/mihomo/blob/v1.19.30/go.mod) · [go.sum](https://github.com/MetaCubeX/mihomo/blob/v1.19.30/go.sum) | 2026-10-10 backfill: five assets verified; original binary unchanged |
| `mipsel-v1.19.31` | [binary release](https://github.com/saymer-alt/mihomo-auto-build/releases/tag/mipsel-v1.19.31) | [tagged source](https://github.com/MetaCubeX/mihomo/tree/v1.19.31) · [source archive](https://github.com/MetaCubeX/mihomo/archive/refs/tags/v1.19.31.tar.gz) · [go.mod](https://github.com/MetaCubeX/mihomo/blob/v1.19.31/go.mod) · [go.sum](https://github.com/MetaCubeX/mihomo/blob/v1.19.31/go.sum) | 2026-10-10 backfill: five assets verified; original binary unchanged |
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
- [x] All nine releases (`v1.19.24`–`v1.19.32`) have five assets each, including GPL-3.0 and version-specific third-party license notices; binary IDs/digests were preserved during historical backfill.
- [ ] **Complete Corresponding Source** of the actual MIPSel binary is independently verified:
      exact build script revision, module versions and replacements, generated files,
      any compiled/embedded assets, and modification/install/run scripts where applicable.
- [x] Version-correct **upstream source entry points** were appended next to
      each published binary on all nine GitHub Release pages
      ([verified publication](https://github.com/saymer-alt/mihomo-auto-build/actions/runs/38130836000)).
      This does **not** establish the historic builder commit or complete source.
- [ ] Source download availability, public access, matching tagged trees and
      continued accessibility are verified for every release.
- [ ] Applicable GPL/LGPL/MPL obligations (see [20 module indicators](COPYLEFT-REVIEW.md), including any conditions specific to
      static linking/relinking or file-level source disclosures) have been
      reviewed against **actually incorporated code**, not simply 112 build-info modules.
- [x] Historical missing checksum and license/attribution notice **assets** were added by reviewed per-version `plan → publish` runs; original binary IDs/sizes/digests remained unchanged.
      This does **not** close source-offer completeness or applicable license obligations.

### Limitations and safety

- No legal conclusion is made about compatibility of the 20 copyleft
  indicators in `v1.19.32` or exact obligations of particular modules.
- Upstream source and the current workflow are publicly readable, but this
  document does **not** assert that a release tarball containing all source,
  all build scripts or an exact binary-rebuild proof has been published.
- The `v1.19.24`–`v1.19.31` releases predate notice automation; their missing
  four sidecar/notice assets were added on 2026-10-10 after independent audit.
  Do **not** overwrite or reissue their original binaries or mark full license
  obligations resolved without separate source/linkage review.
- Release descriptions now provide easy-to-find version-specific source
  entry points and disclose the outstanding historical builder-source review.
  Complete Corresponding Source access and GPLv3 §6(d) sufficiency remain
  subject to independent verification.

## Future release verification

The [scheduled build workflow](.github/workflows/build-mihomo-mipsel.yml)
checks upstream once a day. As of this review the upstream latest version
is `v1.19.32`; there is **no later upstream release** on which to validate the
new-version path in production. After the 2026-10-11 license audit,
new builds also fail closed if the MIPSel-selected Go package graph includes
the unresolved GPLv2 go-lzo dependency; this guard does not affect
verification of an existing complete release. The first later upstream
version must pass separate source/licensing review before publication.
Offline tests alone are not a substitute for end-to-end validation.
