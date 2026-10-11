# Historical MIPSel builder provenance map — 2026-10-11

**Evidence map, not a byte-for-byte reproducibility or GPLv3-compliance certificate.**
Read-only inspection; no tags, published binary assets or release descriptions
were modified by this investigation.

## Source and build evidence

| Published release | Upstream tag currently resolves to commit | Matching successful GitHub Actions run | Run's **builder head SHA** | Go compiler in retained run log | Confidence of publication linkage |
| --- | --- | --- | --- | --- | --- |
| [v1.19.24](https://github.com/saymer-alt/mihomo-auto-build/releases/tag/mipsel-v1.19.24) | [a84724665e](https://github.com/MetaCubeX/mihomo/commit/a84724665eb7f989809abe463c05f5723bd24975) | [run 25697696045](https://github.com/saymer-alt/mihomo-auto-build/actions/runs/25697696045) | [285d773903](https://github.com/saymer-alt/mihomo-auto-build/commit/285d77390393be8171bda2615c672bd3290fd2be) | unknown | Run metadata only; logs expired (HTTP 410) |
| [v1.19.25](https://github.com/saymer-alt/mihomo-auto-build/releases/tag/mipsel-v1.19.25) | [5e22035118](https://github.com/MetaCubeX/mihomo/commit/5e22035118d13fa609164670111cc674906bb2a4) | [run 25983416996](https://github.com/saymer-alt/mihomo-auto-build/actions/runs/25983416996) | [873fab2078](https://github.com/saymer-alt/mihomo-auto-build/commit/873fab207826090af46ab821faf477bdd334cb93) | unknown | Run metadata only; logs expired (HTTP 410) |
| [v1.19.26](https://github.com/saymer-alt/mihomo-auto-build/releases/tag/mipsel-v1.19.26) | [fc8c5a24b1](https://github.com/MetaCubeX/mihomo/commit/fc8c5a24b16991f98cd736950c17d1aa306a5041) | [run 26744112086](https://github.com/saymer-alt/mihomo-auto-build/actions/runs/26744112086) | [873fab2078](https://github.com/saymer-alt/mihomo-auto-build/commit/873fab207826090af46ab821faf477bdd334cb93) | unknown | Run metadata only; logs expired (HTTP 410) |
| [v1.19.27](https://github.com/saymer-alt/mihomo-auto-build/releases/tag/mipsel-v1.19.27) | [5184081ac3](https://github.com/MetaCubeX/mihomo/commit/5184081ac327394d9e15fa5d5f9f4a61e723fd94) | [run 27124442698](https://github.com/saymer-alt/mihomo-auto-build/actions/runs/27124442698) | [873fab2078](https://github.com/saymer-alt/mihomo-auto-build/commit/873fab207826090af46ab821faf477bdd334cb93) | unknown | Run metadata only; logs expired (HTTP 410) |
| [v1.19.28](https://github.com/saymer-alt/mihomo-auto-build/releases/tag/mipsel-v1.19.28) | [cbd11db1e1](https://github.com/MetaCubeX/mihomo/commit/cbd11db1e13a75d8e680e0fe7742c95be4cba2be) | [run 28920747623](https://github.com/saymer-alt/mihomo-auto-build/actions/runs/28920747623) | [873fab2078](https://github.com/saymer-alt/mihomo-auto-build/commit/873fab207826090af46ab821faf477bdd334cb93) | unknown | Run metadata only; logs expired (HTTP 410) |
| [v1.19.29](https://github.com/saymer-alt/mihomo-auto-build/releases/tag/mipsel-v1.19.29) | [e26714a181](https://github.com/MetaCubeX/mihomo/commit/e26714a181ac0e2fa803453c0a8e9a9ce94e31cb) | [run 29675518765](https://github.com/saymer-alt/mihomo-auto-build/actions/runs/29675518765) | [873fab2078](https://github.com/saymer-alt/mihomo-auto-build/commit/873fab207826090af46ab821faf477bdd334cb93) | go1.26.5 | Run log confirms version, Go compiler, and creation of release |
| [v1.19.30](https://github.com/saymer-alt/mihomo-auto-build/releases/tag/mipsel-v1.19.30) | [ac017cdd24](https://github.com/MetaCubeX/mihomo/commit/ac017cdd246ce8bd547653d927e7bf77d7ee73d5) | [run 31992381791](https://github.com/saymer-alt/mihomo-auto-build/actions/runs/31992381791) | [873fab2078](https://github.com/saymer-alt/mihomo-auto-build/commit/873fab207826090af46ab821faf477bdd334cb93) | go1.26.6 | Run log confirms version, Go compiler, and creation of release |
| [v1.19.31](https://github.com/saymer-alt/mihomo-auto-build/releases/tag/mipsel-v1.19.31) | [ab405bad5b](https://github.com/MetaCubeX/mihomo/commit/ab405bad5beeeac8b003bb01f60f134f6df54471) | [run 34946811737](https://github.com/saymer-alt/mihomo-auto-build/actions/runs/34946811737) | [873fab2078](https://github.com/saymer-alt/mihomo-auto-build/commit/873fab207826090af46ab821faf477bdd334cb93) | go1.27.1 | Run log confirms version, Go compiler, and creation of release |
| [v1.19.32](https://github.com/saymer-alt/mihomo-auto-build/releases/tag/mipsel-v1.19.32) | [88dcbf7f16](https://github.com/MetaCubeX/mihomo/commit/88dcbf7f1614a67c3b36b848ee3592dfa92ada36) | [run 36845065651](https://github.com/saymer-alt/mihomo-auto-build/actions/runs/36845065651) | [873fab2078](https://github.com/saymer-alt/mihomo-auto-build/commit/873fab207826090af46ab821faf477bdd334cb93) | go1.27.1 | Run log confirms version, Go compiler, and creation of release |

**How checked:** for each of nine existing GitHub Releases, retrieved `published_at`
and searched **successful Build Mihomo for MIPSel** workflow runs on that date.
The listed run immediately precedes release publication; its head SHA is
the actual GitHub Actions source revision at that run. Both historic builder
commits `285d773...` and `873fab...` remain accessible and include the
historical `.github/workflows/build-mihomo-mipsel.yml` source.

For v1.19.29–v1.19.32, retained logs independently confirm `=== Cloning
Mihomo vX ===`, the exact runner Go version, the compilation step and
`Release ready at .../mipsel-vX`. For v1.19.24–v1.19.28,
GitHub Actions run records still show the completed build step with
`conclusion: success`, but raw job logs returned HTTP 410 (retention
expired), so the specific version/compiler cannot be independently
recovered from those logs. **Do not treat proximity of the workflow
run to a Release publication as a cryptographic build-to-asset attestation.**

The upstream source commit in column 2 is the **current resolution of
the version tag**, obtained via GitHub refs API on 2026-10-11.
Historic Actions logs only show cloning that named tag, not the
resolved commit at build time. Therefore, source tree identity in the
old build is strong but not independently attested unless corroborated
by a signed digest or other build provenance.

## Builder source and limits

- Download repository source as it existed at the recorded **Actions run
  head SHA** using `https://github.com/saymer-alt/mihomo-auto-build/archive/<full-run-head-sha>.zip`.
  For the original build use that historic workflow rather than current `main`.
- Download Mihomo's version-specific upstream tag source, inspect its
  `go.mod`, `go.sum`, `replace` directives and required modules. A
  `go version -m <binary>` dump may independently identify the compiler
  version and effective module build info where job logs are unavailable.
- The historical workflow selected the latest **stable Go** dynamically.
  For v1.19.24–v1.19.28 the exact Go compiler is **not confirmed** from
  retained logs; do not invent it.
- Builds had time-stamped `constant.BuildTime` and compiler/toolchain
  dependencies. GitHub asset SHA-256 establishes binary integrity, but
  neither source correspondence nor reproducible compilation by itself.
- Complete Corresponding Source obligations also concern dependency
  sources and applicable build/install/modify scripts. The linked-symbol
  and GPLv2-only `go-lzo` question remains documented in
  [Issue #8](https://github.com/saymer-alt/mihomo-auto-build/issues/8).
- These historical provenance links are **supporting evidence only**.
  Their availability is not a legal conclusion that source delivered
  to recipients meets GPLv3 §6(d) for every binary.

## Next evidence steps

1. Record `go version -m` from the actual five older binaries to
   confirm missing compiler versions without rebuilding them.
2. For v1.19.32, compare a diagnostic unstripped rebuild against
   the *selected MIPSel package graph* and inspect retained `go-lzo`
   symbols; see [read-only audit PR #25](https://github.com/saymer-alt/mihomo-auto-build/pull/25).
3. Confirm real upstream source commit and dependency source availability
   for all versions; decide whether a consolidated corresponding-source
   archive or mirror is required, especially for historical releases.
4. Keep [Issue #8](https://github.com/saymer-alt/mihomo-auto-build/issues/8)
   OPEN until linked GPLv2/ GPLv3 compatibility and CCS sufficiency
   have been independently established.
