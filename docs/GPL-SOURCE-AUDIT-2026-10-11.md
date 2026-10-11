# MIPSel GPL/LGPL/MPL technical audit — 2026-10-11

**Status: evidence and risk triage, NOT a legal compliance certificate.**
Scope: `mipsel-v1.19.24`–`v1.19.32`, source/notice automation
and pinned upstream license samples. No published release assets,
binaries, tags or live equipment were altered.

## Verified release state

- GitHub Releases API: **9/9 releases contain five assets** each
  (original binary, SHA-256, exact upstream GPL-3.0 LICENSE,
  dependency license summary and full notices). The historical
  8-release backfill and stable binary IDs/digests are documented
  in [Issue #8](https://github.com/saymer-alt/mihomo-auto-build/issues/8#issuecomment-6102988561).
  This audit independently checked asset metadata, not binary bytes.
- The original nine Release descriptions lacked version-specific source
  pointers. On 2026-10-11, [PR #23](https://github.com/saymer-alt/mihomo-auto-build/pull/23)
  appended exact upstream tag archives and go.mod/go.sum pointers to
  **all nine**, plus explicit GPLv2 errata to the **seven affected releases**
  (v1.19.26–v1.19.32). All original assets were unchanged and the
  [publish job](https://github.com/saymer-alt/mihomo-auto-build/actions/runs/38130836000)
  succeeded. The exact historical builder commit and Complete Corresponding
  Source sufficiency are **still not established**.
- The [build workflow](../.github/workflows/build-mihomo-mipsel.yml)
  cross-compiles with `CGO_ENABLED=0 GOOS=linux GOARCH=mipsle
  GOMIPS=softfloat`, `actions/setup-go@v5` selecting Go `stable`,
  and embeds a build-time timestamp. Reconstructing the **exact** old
  builder commit and toolchain is outstanding.

## Updated hard evidence — 2026-10-11

A [SHA-256-verified original `mipsel-v1.19.32` ELF](https://github.com/saymer-alt/mihomo-auto-build/releases/tag/mipsel-v1.19.32)
was inspected **without rebuilding or modifying it**:
[`audit_published_elf.go`](../scripts/audit_published_elf.go) decoded the
runtime `.gopclntab` and found **five actual Go function names** from
`github.com/rasky/go-lzo`, including `Decompress1X` and
`Decompress1X.func1`. A separate *unstripped diagnostic rebuild* using
the exact upstream `v1.19.32` tag, Go `1.27.1` and MIPSel flags retained
**seven `go-lzo` linker symbols**. The verified source import chain is:

`mihomo → config → adapter/outbound → transport/openvpn → go-lzo`

Source: [OpenVPN LZO adapter](https://github.com/MetaCubeX/mihomo/blob/v1.19.32/transport/openvpn/lzo.go),
which directly calls `lzo.Decompress1X` for LZO-compressed packets.
Evidence: [successful read-only audit](https://github.com/saymer-alt/mihomo-auto-build/actions/runs/38132608435)
and [PR #25](https://github.com/saymer-alt/mihomo-auto-build/pull/25).
For that published version, presence of Go function metadata inside the
original ELF is **confirmed**, no longer only a conjecture from `go.mod`.
Other six affected historic binaries have not undergone the same ELF
function audit individually.

**No alternate grant identified:** in
[go-lzo issue #6](https://github.com/rasky/go-lzo/issues/6#issuecomment-581445627),
its maintainer explicitly declined dual licensing because the Go port
was based on GPL-covered original C source. The pinned README/LICENSE
declare GPLv2; no GPLv2-or-later permission was established.
The [FSF compatibility FAQ](https://www.gnu.org/licenses/gpl-faq.en.html#v2v3Compatibility)
states GPLv2-only cannot ordinarily be combined with GPLv3 code.
A legal conclusion and rights-holder analysis still require qualified
review; the technical risk is now **high**, rather than hypothetical.

**Safety:** production new-build blocking is already enabled for an
MIPSel build importing `go-lzo`; no binary assets were modified.
Safe long-term remediation requires upstream OpenVPN LZO code replacement
with a properly licensed compatible implementation, or a documented
authorization from *all relevant* rights holders, not merely renaming
the license. Do not silently drop OpenVPN functionality to pass the gate.

## P1: confirmed wrong license label for go-lzo

In `v1.19.32`, the published `THIRD_PARTY_LICENSES` summary labels
`github.com/rasky/go-lzo@v0.0.0-20200203143853-96a758eda86e`
as **LGPL-2.1**, but the exact upstream
[README](https://github.com/rasky/go-lzo/blob/96a758eda86e/README.md)
says **GPLv2** and its
[`LICENSE.gpl`](https://github.com/rasky/go-lzo/blob/96a758eda86e/LICENSE.gpl)
is headed `GNU GENERAL PUBLIC LICENSE / Version 2, June 1991`.
Only this LICENSE was found at the referenced commit. A license text
was shipped, but its automated classification was wrong.

Root cause: `collect_upstream_licenses.py::classify()` searches the
first 8 KiB for the phrase `GNU Lesser General Public License`
**before** identifying the document as GPL. Canonical GPLv2's preamble
mentions LGPL as a separate license and triggers this false positive.

**Impact:** the old automatically generated `14 GPL / 2 LGPL /
4 MPL-mixed` table is misleading. With the known correction alone,
candidate counts become **15 GPL / 1 LGPL / 4 MPL-mixed**, still
not proof of linked code. Separate download/inspection of all nine
release summaries in [PR #23's verified preflight](https://github.com/saymer-alt/mihomo-auto-build/actions/runs/38130787419)
found the *same proven mislabel* in **seven** versions (v1.19.26–v1.19.32);
v1.19.24 and v1.19.25 do not list go-lzo.

**Compatibility risk:** if GPLv2-only source is actually incorporated
into a combined GPLv3 executable, these terms can be incompatible.
A real [read-only Go build-graph check](https://github.com/saymer-alt/mihomo-auto-build/actions/runs/38131113277)
using the exact upstream tag and `GOOS=linux GOARCH=mipsle GOMIPS=softfloat
CGO_ENABLED=0` confirmed the `github.com/rasky/go-lzo` **package is in the
selected Go import graph**. This is stronger than `go.mod` membership, but
does not independently prove final linked symbols or legal compatibility;
no legal violation is asserted. The license grant and any exceptions
still need a qualified compatibility assessment.
Reference: [GNU GPL compatibility FAQ](https://www.gnu.org/licenses/gpl-faq.en.html#v2v3Compatibility).

[PR #21](https://github.com/saymer-alt/mihomo-auto-build/pull/21)
is now **merged**: the classifier identifies the actual GPLv2 text by
its canonical header, with regression tests and a strictly limited
legacy-asset compatibility path. Existing historical summaries/full
notices are preserved byte-for-byte; regeneration of corrected notices
was [tested against the actual v1.19.32 binary](https://github.com/saymer-alt/mihomo-auto-build/actions/runs/38131232750).
Any drift other than the exactly documented go-lzo label still fails closed.
The new build workflow blocks a *new* MIPSel binary when its import
graph includes the unresolved GPLv2 go-lzo dependency; previously
published versions are not changed.

## Remaining corresponding-source and license audit

1. **Per-version delivery:** establish publicly reachable source
   archives, effective `go.mod/go.sum` replacements, generated/embedded
   data and appropriate build/install/modify instructions, then add
   verifiable links directly next to the binary on each of nine Release
   pages. Identify *actual* builder commit from historical provenance;
   do not substitute present `main` or infer it from dates. GitHub
   Source pointers are now present on **9/9 release descriptions**, but
   the exact historical builder commits and actual CCS completeness
   remain open for verification.
2. **Actual code/linkage:** `go list -deps` has now shown that the
   `go-lzo` package is imported by the MIPSel-selected Go package
   graph of v1.19.32. Next resolve reachability and linker elimination,
   final object-code inclusion, generated/embedded source components
   and whether GPLv2/GPLv3 may lawfully be combined. Repeat provenance
   checks across historical versions rather than extrapolating.
3. **Module license provenance:** review exact effective source
   versions, file SPDX headers, exceptions and optional grants for
   all 20 copyleft-indicator modules and all versions actually
   published. Sample pinned LICENSEs were checked:
   [EasyTier LGPL-3.0](https://github.com/EasyTier/EasyTier/blob/3d0c9c3ca5e2/easytier-go/LICENSE),
   [hashicorp/golang-lru MPL-2.0](https://github.com/hashicorp/golang-lru/blob/v2.0.7/LICENSE),
   [mipstack MPL-2.0](https://github.com/MetaCubeX/mipstack/blob/961d4b1c1983/LICENSE),
   [zerotier-go MPL-2.0](https://github.com/MetaCubeX/zerotier-go/blob/13fa6f45da5f/LICENSE).
   This is a *sample*, not a full module-by-module audit.
4. **Build provenance and CCS:** record Go version, action SHA,
   upstream tag commit, effective dependency source digests,
   timestamps, source and scripts used for each published artifact.
   A release SHA-256 proves bit integrity, not source completeness
   or reproducibility.
5. **Legal evaluation:** after incorporation and source evidence,
   assess GPLv3 §6(d), GPLv2-only compatibility, applicable
   LGPL relinking requirements and MPL 2.0 source/notice duties.
   Reference: [FSF GPL FAQ](https://www.gnu.org/licenses/gpl-faq.en.html)
   and [Mozilla MPL FAQ](https://www.mozilla.org/en-US/MPL/2.0/FAQ/).
   Obtain specialist advice if distributing an actually combined
   incompatible-license binary cannot be ruled out.

## Disposition

**Observed:** the incorrect license label was verified in seven
published summaries and corrected with on-page errata; nine source
entry-point link sections now exist; the classifier and narrowly
guarded historic-notice checks were merged after end-to-end CI.
The published v1.19.32 ELF itself retains five `go-lzo` functions,
and a diagnostic rebuild retains seven symbols. Historic builder run
revisions and all compiler versions are mapped in
[the provenance report](HISTORICAL-BUILD-PROVENANCE-2026-10-11.md).
A byte-identical rebuild, historical source correspondence, legal
GPLv2/GPLv3 compatibility and Complete Corresponding Source
sufficiency remain open.

**Action:** keep [Issue #8](https://github.com/saymer-alt/mihomo-auto-build/issues/8)
OPEN, prioritize legal compatibility and exact historical build-source
evidence. The new-build guard should remain until resolved.
Do not claim full GPL compliance from CI PASS or release asset count.
