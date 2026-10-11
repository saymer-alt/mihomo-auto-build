# Ready-to-submit upstream issue — OpenVPN LZO GPLv2-only module

**Target:** https://github.com/MetaCubeX/mihomo/issues/new

**Title:** `OpenVPN comp-lzo includes GPLv2-only go-lzo: tested MIT LZO1X replacement candidate`

**Submission state (2026-10-11):** NOT submitted. The GitHub integration connected to
`saymer-alt` received HTTP **403: Resource not accessible by integration**
when attempting to create this issue at `MetaCubeX/mihomo`. An owner-authenticated
browser session or GitHub token with the appropriate rights must submit it.
This file is only an approved owner-requested technical draft; **do not**
describe this document as an upstream PR or accepted fix.

## Upstream issue body (copy everything below)

The OpenVPN `comp-lzo` implementation in upstream Mihomo `v1.19.32` uses
`github.com/rasky/go-lzo@96a758eda86e` directly via
[`transport/openvpn/lzo.go`](https://github.com/MetaCubeX/mihomo/blob/v1.19.32/transport/openvpn/lzo.go),
calling `lzo.Decompress1X` on packet header `0x66`.
The pinned [README](https://github.com/rasky/go-lzo/blob/96a758eda86e/README.md)
and [LICENSE.gpl](https://github.com/rasky/go-lzo/blob/96a758eda86e/LICENSE.gpl)
declare **GPL version 2** with no verified "or later" permission.
Its author [declined dual licensing in 2020](https://github.com/rasky/go-lzo/issues/6#issuecomment-581445627)
because the Go port reproduces GPL-covered C source.
Mihomo's source tag declares **GPLv3**. This is a serious
GPLv2-only/GPLv3-combination risk for redistributed Go binaries,
not a final legal opinion.

**Actual inclusion independently checked:** after SHA-256 verification,
the original published MIPSel `v1.19.32` executable's Go `.gopclntab`
contains **five go-lzo functions**, including `Decompress1X`.
A Go 1.27.1 MIPSel diagnostic rebuild retains seven symbols. Source
and audit: https://github.com/saymer-alt/mihomo-auto-build/actions/runs/38132608435

**Tested MIT replacement candidate:**
`github.com/anchore/go-lzo@v0.1.0` has a published MIT LICENSE and
independent `Decompress(src, dst)` implementation. A reproducible,
ephemeral patch replaces only the OpenVPN `lzo.go` decoder and uses
bounded output-buffer growth (hard 1 MiB decompression cap, subject
to review for OpenVPN MTU/packet limits). The original OpenVPN
`0xFA` / `0x66` frame handling is preserved.

**End-to-end CI proof:** on exact Mihomo tag `v1.19.32` at commit
`88dcbf7f1614a67c3b36b848ee3592dfa92ada36`, OpenVPN
compressed-frame tests pass; an actual stripped MIPSel full
Mihomo build succeeds; `anchore/go-lzo` appears in the
selected package dependency graph while `rasky/go-lzo` is
absent. No binary was released or upstream changed.

- [Temporary source patch script](https://github.com/saymer-alt/mihomo-auto-build/blob/main/experiments/mit-lzo-openvpn/patch_mihomo_lzo.py)
- [Successful CI](https://github.com/saymer-alt/mihomo-auto-build/actions/runs/38133325622)
- [Full technical details and testing limits](https://github.com/saymer-alt/mihomo-auto-build/blob/main/docs/OPENVPN-LZO-MIT-REMEDIATION-2026-10-11.md)

**Request:** please review replacing `rasky/go-lzo` with a
permission-compatible implementation for OpenVPN, retaining
compressed-packet interoperability, independent provenance review,
fuzzing, and output-memory limits. The current temporary patch is a
tested starting point, not a merge-ready upstream PR or a legal
certification. Happy to adapt to upstream review requirements.
