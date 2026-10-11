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
- All **nine current Release descriptions** were inspected. **None**
  contains explicit, version-specific instructions to obtain complete
  corresponding source or the actual historical builder commit.
  [SOURCE-AVAILABILITY.md](../SOURCE-AVAILABILITY.md) separately maps
  upstream tags and general build tooling, but this alone is not a
  verified Complete Corresponding Source offer.
- The [build workflow](../.github/workflows/build-mihomo-mipsel.yml)
  cross-compiles with `CGO_ENABLED=0 GOOS=linux GOARCH=mipsle
  GOMIPS=softfloat`, `actions/setup-go@v5` selecting Go `stable`,
  and embeds a build-time timestamp. Reconstructing the **exact** old
  builder commit and toolchain is outstanding.

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
not proof of linked code. No audit of other eight version-specific
summaries for this problem has been completed yet.

**Compatibility risk:** if GPLv2-only source is actually incorporated
into a combined GPLv3 executable, these terms can be incompatible.
However, `go.mod` and `go version -m` list module-graph members,
**not** linked object code. Inclusion of go-lzo in the MIPSel binary
is **not established**, so no legal violation is asserted.
The author's declaration and license grant must also be assessed
for any additional permissions or exceptions.
Reference: [GNU GPL compatibility FAQ](https://www.gnu.org/licenses/gpl-faq.en.html#v2v3Compatibility).

[Draft PR #21](https://github.com/saymer-alt/mihomo-auto-build/pull/21)
contains a targeted header-aware classifier correction and two
offline regression tests. **Do not merge it immediately.** The
scheduled release workflow recalculates notices for complete old
releases; corrected generated text will differ from the immutable
published summary and the existing publisher correctly fails closed.
An owner-approved, auditable **additive erratum/correction strategy**
is needed, retaining original asset IDs/digests and original binaries.
Never silently overwrite old summaries or turn off mismatch checks.

## Remaining corresponding-source and license audit

1. **Per-version delivery:** establish publicly reachable source
   archives, effective `go.mod/go.sum` replacements, generated/embedded
   data and appropriate build/install/modify instructions, then add
   verifiable links directly next to the binary on each of nine Release
   pages. Identify *actual* builder commit from historical provenance;
   do not substitute present `main` or infer it from dates. GitHub
   API currently shows **0/9 source-linked descriptions**.
2. **Actual package inclusion:** using the tagged source and correct
   compilation environment, run `go list -deps -json` against the
   *actual built entry package* (not all repo packages). Map imported
   packages/files to module roots under the MIPSel GOOS/GOARCH/tags,
   especially `go-lzo`. Separately verify code generation and
   stripped executable characteristics. Do not infer linkage from
   direct vs indirect `go.mod` entries.
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

**Observed:** published notice files exist; one confirmed GPL/LGPL
classification defect; nine source-pointer gaps; source/toolchain and
linked-code proofs incomplete.

**Action:** keep [Issue #8](https://github.com/saymer-alt/mihomo-auto-build/issues/8)
OPEN, prioritize the go-lzo inclusion/compatibility check, establish
a safe erratum strategy and only then promote the classifier fix.
Do not claim full GPL compliance from CI PASS or release asset count.
