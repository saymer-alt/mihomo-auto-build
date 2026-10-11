# Copyleft evidence review — Mihomo MIPSel v1.19.32

**Scope:** offline inventory from `THIRD_PARTY_LICENSES-v1.19.32.txt` and the actual
published binary's Go build-info, audited on 2026-10-10. **Not legal advice,
not a determination that all modules below are linked, or that all licensing
obligations have been met.** This is a triage list for [Issue #8](https://github.com/saymer-alt/mihomo-auto-build/issues/8).

## Evidence, not a conclusion

- Report: **112 modules in the Go build graph** (upstream main module + 111 deps),
  with **20 copyleft indicators** (original auto-classification: GPL: 14,
  LGPL: 2, MPL/mixed: 4). A **confirmed classifier error** means those
  category counts are not reliable: `rasky/go-lzo` was wrongly labeled
  LGPL-2.1, while its exact upstream README and LICENSE.gpl say GPLv2.
  If all other labels stand, the corrected grouping would be 15 GPL,
  1 LGPL and 4 MPL/mixed. These remain *build-graph indicators*,
  not proof of final linked symbols. A [MIPSel-targeted Go package graph check](https://github.com/saymer-alt/mihomo-auto-build/actions/runs/38131113277)
  did independently find the `go-lzo` package among selected imports for
  v1.19.32. Subsequently, [PR #25](https://github.com/saymer-alt/mihomo-auto-build/pull/25)
  proved **five go-lzo functions are retained in the original published
  stripped v1.19.32 ELF's Go function metadata**; a diagnostic rebuild
  has seven linked symbols. Exact legal compatibility and obligations
  remain unresolved.
- Go build-info is **not a linker object map**. It can include modules whose code
  is not present in a particular binary. The inventory alone cannot establish
  a license's applicability or static/dynamic combination conditions.
- Full collected license text is published as
  [THIRD_PARTY_NOTICES-v1.19.32.txt](https://github.com/saymer-alt/mihomo-auto-build/releases/tag/mipsel-v1.19.32).
  Automatic classification does **not** establish license compatibility.
- Source distribution: see [SOURCE-AVAILABILITY.md](SOURCE-AVAILABILITY.md)
  for exact tagged sources, build recipe, GPL §6(d) gaps and historical versions.

## Items requiring manual provenance and linkage review

| Effective module from build info | Heuristic license | Family | Review status |
| --- | --- | --- | --- |
| `github.com/easytier/easytier/easytier-go@v0.0.0-20260910071355-3d0c9c3ca5e2` | `LGPL-3.0` | LGPL | Unverified: inclusion and obligations |
| `github.com/enfein/mieru/v3@v3.38.0` | `GPL-3.0` | GPL | Unverified: inclusion and obligations |
| `github.com/hashicorp/golang-lru/v2@v2.0.7` | `MPL-2.0` | MPL | Unverified: inclusion and obligations |
| `github.com/metacubex/fswatch@v0.1.1` | `GPL-3.0-or-later` | GPL | Unverified: inclusion and obligations |
| `github.com/metacubex/mihomo@v1.19.32 [upstream main module]` | `GPL-3.0` | GPL | Unverified: inclusion and obligations |
| `github.com/metacubex/mipstack@v0.0.0-20260930071539-961d4b1c1983` | `MPL-2.0` | MPL | Unverified: inclusion and obligations |
| `github.com/metacubex/randv2@v0.2.0` | `GPL-3.0` | GPL | Unverified: inclusion and obligations |
| `github.com/metacubex/sing-mux@v0.3.12` | `GPL-3.0-or-later` | GPL | Unverified: inclusion and obligations |
| `github.com/metacubex/sing-quic@v0.0.0-20260904234848-1c242664697a` | `GPL-3.0-or-later` | GPL | Unverified: inclusion and obligations |
| `github.com/metacubex/sing-shadowsocks2@v0.2.8` | `GPL-3.0-or-later` | GPL | Unverified: inclusion and obligations |
| `github.com/metacubex/sing-shadowsocks@v0.2.13` | `GPL-3.0-or-later` | GPL | Unverified: inclusion and obligations |
| `github.com/metacubex/sing-tun@v0.4.27` | `GPL-3.0-or-later` | GPL | Unverified: inclusion and obligations |
| `github.com/metacubex/sing-vmess@v0.2.5` | `GPL-3.0-or-later` | GPL | Unverified: inclusion and obligations |
| `github.com/metacubex/sing-wireguard@v0.0.0-20260826105301-c3ae17d19f9e` | `GPL-3.0` | GPL | Unverified: inclusion and obligations |
| `github.com/metacubex/sing@v0.5.8` | `GPL-3.0-or-later` | GPL | Unverified: inclusion and obligations |
| `github.com/metacubex/yamux@v0.0.0-20250918083631-dd5f17c0be49` | `BSD-3-Clause+MPL-2.0` | MPL | Unverified: inclusion and obligations |
| `github.com/metacubex/zerotier-go@v0.0.0-20260813124750-13fa6f45da5f` | `MPL-2.0` | MPL | Unverified: inclusion and obligations |
| `github.com/rasky/go-lzo@v0.0.0-20200203143853-96a758eda86e` | **GPL-2.0** (upstream README and `LICENSE.gpl` at pinned commit; published summary **incorrectly says LGPL-2.1**) | GPLv2 | **Original published v1.19.32 ELF retains 5 go-lzo functions; GPLv2/GPLv3 compatibility unresolved (P1)** |
| `github.com/sina-ghaderi/poly1305@v0.0.0-20220724002748-c5926b03988b` | `GPL-3.0` | GPL | Unverified: inclusion and obligations |
| `github.com/sina-ghaderi/rabaead@v0.0.0-20220730151906-ab6e06b96e8c` | `GPL-3.0` | GPL | Unverified: inclusion and obligations |

## Review work to finish before closing Issue #8

1. For each flagged effective module, independently inspect original source
   distribution and SPDX/license notices at the **exact version and replacements**
   used by the binary. Record copyright owner, any exceptions, alternative
   licenses, additional NOTICE/PATENTS requirements and relevant commit/source URL.
2. Determine which packages and files actually contribute code to the compiled
   `GOOS=linux GOARCH=mipsle GOMIPS=softfloat CGO_ENABLED=0` binary.
   A reproducible build and Go package/link evidence are required; the build-info
   module graph is deliberately over-inclusive.
3. Evaluate **GPLv3 / LGPL-2.1 / LGPL-3.0 / MPL-2.0** obligations in context
   (combined binaries, file-level disclosures, version-appropriate source,
   possible relinking/modified-library provisions). Do **not** guess from a
   one-line license classifier. The upstream main Mihomo module is GPL-3.0.
4. Make Complete Corresponding Source available on equivalent public terms
   with clear version-specific directions next to each binary per
   [GPLv3 §6(d)](https://www.gnu.org/licenses/gpl-3.0.html).
   If further source material, scripts or information are required, provide them
   rather than relying on a broad `go.mod` link.
5. Verify and record the eight legacy releases separately; do not touch
   existing binary objects/digests. Require individual audit and authorization
   before adding missing files.

**Updated 2026-10-11:** full notices and checksum assets exist for **all nine**
published versions. The original `go-lzo` classification was wrong
in seven versions (v1.19.26–v1.19.32); precise errata have since been
added to their Release descriptions, with original summary/notice
assets retained. The corrected classifier and strict legacy verifier
were merged via [PR #21](https://github.com/saymer-alt/mihomo-auto-build/pull/21).
The pinned README/LICENSE declare GPLv2 (no "or later" grant was
identified). See [the evidence audit](docs/GPL-SOURCE-AUDIT-2026-10-11.md).
**Actual go-lzo function inclusion in v1.19.32 is confirmed, but GPLv2/GPLv3
legal compatibility and GPLv3 Complete Corresponding Source sufficiency
remain unresolved**. [Issue #8](https://github.com/saymer-alt/mihomo-auto-build/issues/8)
must remain OPEN.

## Safe OpenVPN LZO replacement research (2026-10-11)

A [tested MIT OpenVPN LZO replacement](docs/OPENVPN-LZO-MIT-REMEDIATION-2026-10-11.md) has passed a read-only experiment on
the actual Mihomo `v1.19.32` source: MIT-licensed
`anchore/go-lzo@v0.1.0`, OpenVPN compressed-frame tests and a
complete cross-compiled MIPSel ELF without `rasky/go-lzo`
in the effective package graph.
[GitHub Actions SUCCESS](https://github.com/saymer-alt/mihomo-auto-build/actions/runs/38133325622).

**No published binary or production builder was changed.**
The production new-build safety gate remains enabled until upstream
reviews and integrates an appropriate implementation, licensing
and source-delivery obligations are evaluated, and interoperability
is independently validated. Existing historical releases remain
a separate compliance-review concern in [Issue #8](https://github.com/saymer-alt/mihomo-auto-build/issues/8).
