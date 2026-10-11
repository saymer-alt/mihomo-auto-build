# P1 — OpenVPN LZO1X GPLv2-only remediation candidate (2026-10-11)

**Status:** successfully tested **experimental source change**, **NOT deployed** to
the published Mihomo release workflow, **NOT adopted upstream** and **NOT a
final legal-compliance determination**.

## Confirmed original risk

- Released `mipsel-v1.19.32` is SHA-256-verified, with **five**
  `github.com/rasky/go-lzo` functions in the actual stripped ELF's
  `.gopclntab`. A pinned Go 1.27.1 MIPSel diagnostic rebuild retained
  **seven** `go-lzo` linker symbols.
- The selected upstream import chain is:
  `mihomo/config → adapter/outbound → transport/openvpn → go-lzo`.
  Original source
  [`transport/openvpn/lzo.go`](https://github.com/MetaCubeX/mihomo/blob/v1.19.32/transport/openvpn/lzo.go)
  invokes `lzo.Decompress1X` for `0x66` OpenVPN compressed packets.
- The pinned [original library README](https://github.com/rasky/go-lzo/blob/96a758eda86e/README.md)
  and [LICENSE.gpl](https://github.com/rasky/go-lzo/blob/96a758eda86e/LICENSE.gpl)
  declare GPLv2. Its original maintainer
  [explicitly refused dual licensing](https://github.com/rasky/go-lzo/issues/6#issuecomment-581445627)
  due to a port of GPL code.
- Per the [GNU GPL FAQ](https://www.gnu.org/licenses/gpl-faq.en.html#v2v3Compatibility),
  GPLv2-only and GPLv3 cannot ordinarily be combined into one
  redistributed program. Scope/permissions remain a legal matter; this
  technical evidence is **not a declaration that a legal violation has
  conclusively been established**.

## MIT replacement candidates actually checked

The [Anchore go-lzo library v0.1.0](https://github.com/anchore/go-lzo/tree/v0.1.0)
has an **MIT LICENSE** (copyright Anchore, Inc.) and exposes
`Decompress(srcBytes, dstBytes []byte) (outSize int, err error)`.
The implementation claims derivation from Linux format documentation and
the MIT-licensed `lzokay` project. It is Go 1.24+, compatible with the
Go 1.27.1 release toolchain.

A separate test-only **MIT-licensed LZO1X compressor**
[`github.com/woozymasta/lzo v0.3.2`](https://github.com/WoozyMasta/lzo)
generated compressed test cases. It was used for experiments only and
is not required by the actual candidate replacement.

**API caveat:** unlike `rasky/go-lzo.Decompress1X`, the Anchore
decoder requires a *caller-owned output buffer*. This is not a
one-line import substitution. The
[temporary patch](../experiments/mit-lzo-openvpn/patch_mihomo_lzo.py)
implements exponential buffer growth only on
`ErrOutputOverrun`, with a hard **1 MiB output cap** per packet to
mitigate decompression-bomb memory exhaustion. The cap should be
reviewed against the actual OpenVPN protocol/MTU behavior and expected
deployments before adoption.

## Tests and reproducible proof-of-concept

[CI SUCCESS — full experimental upstream integration](https://github.com/saymer-alt/mihomo-auto-build/actions/runs/38133325622),
[PR #28 MERGED](https://github.com/saymer-alt/mihomo-auto-build/pull/28).

1. Created a throwaway test module with only the MIT Anchore decoder
   and MIT WoozyMasta encoder. Round-trip decompression passed for
   different LZO1X compressed contents, OpenVPN `0xFA`/ `0x66`
   framing, independent literal/end-marker fixture, malformed inputs
   and bounded-output rejection.
2. Cross-compiled this test module for **`CGO_ENABLED=0 GOOS=linux
   GOARCH=mipsle GOMIPS=softfloat`** (32-bit MIPS ELF).
3. Checked out exact upstream Mihomo tag `v1.19.32` and validated
   commit `88dcbf7f1614a67c3b36b848ee3592dfa92ada36`.
   Applied only a temporary edit to
   `transport/openvpn/lzo.go`, added an OpenVPN compressed-frame test,
   and fetched **`anchore/go-lzo@v0.1.0`**. This checkout was
   discarded after CI; the public upstream repo was not changed.
4. Upstream `transport/openvpn` smoke tests passed.
   The selected **full Mihomo** MIPSel package graph had
   `github.com/anchore/go-lzo` and **no `github.com/rasky/go-lzo`**.
5. A full **statically linked, stripped, 32-bit MIPSel Mihomo**
   binary successfully compiled from the experimentally patched
   checkout. The binary's Go build info contains the new
   `anchore/go-lzo v0.1.0` dependency. **It was not uploaded,
   distributed or installed.**

## Criteria BEFORE lifting the production new-build guard

- [x] Read original GPLv2-only terms, check author licensing refusal
- [x] Identify MIT candidate and review its published LICENSE and API
- [x] Test decompression and OpenVPN packet framing without GPLv2 source
- [x] Test patched actual OpenVPN package and full MIPSel build
- [x] Verify `rasky/go-lzo` is absent in the patched production graph
- [ ] Submit patch to **MetaCubeX/mihomo upstream** and receive review;
      preserve OpenVPN LZO capability and assess the 1 MiB cap
- [ ] Add real OpenVPN server interoperability / compressed packet fixtures,
      malformed input fuzzing, performance and memory comparisons
- [ ] Verify MIT library's provenance/rights and required third-party
      license notices for production redistribution
- [ ] Merge approved upstream change to a new pinned source version,
      confirm exact Go build info, source availability, and complete
      corresponding source publication before releasing a **new** binary
- [ ] Separately address legal status of the seven historic published
      versions and remaining 20 copyleft module indicators

**Do not** simply rewrite existing `v1.19.24–v1.19.32` Releases,
overwrite healthy binaries, rename an upstream GPLv2 license, or disable
the production GPLv2 inclusion guard based on this proof-of-concept.
The original release workflow remains protected. The project-wide
source/license review remains in
[Issue #8](https://github.com/saymer-alt/mihomo-auto-build/issues/8).
