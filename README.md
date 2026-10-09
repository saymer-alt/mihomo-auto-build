# mihomo-auto-build

Automated builds of [Mihomo](https://github.com/MetaCubeX/mihomo) (Clash Meta) for **MIPSel (softfloat)** routers and embedded Linux devices, produced and published by GitHub Actions.

Upstream Mihomo publishes official binaries for many platforms, but not for `mipsle / GOMIPS=softfloat` — the combination required by MT7621-class MIPSel routers. This repository builds that target from source on every upstream release.

## What it does

A scheduled workflow ([`build-mihomo-mipsel.yml`](.github/workflows/build-mihomo-mipsel.yml), daily at 03:00 UTC, manual dispatch enabled):

1. Reads the latest upstream Mihomo release (` vX.Y.Z`, strict semver check).
2. Inspects the existing publication state and builds **only what is missing or invalid** — a healthy released binary is never overwritten (`scripts/release_assets.py` publication state machine).
3. Builds from the upstream source tag:
   `CGO_ENABLED=0 GOOS=linux GOARCH=mipsle GOMIPS=softfloat`, with `-trimpath -ldflags "-s -w"` and a stamped version string.
4. Publishes release assets on a `mipsel-vX.Y.Z` tag and verifies SHA-256 digests before and after upload.

## Releases and assets

Each upstream version gets a release tagged `mipsel-vX.Y.Z` with:

- `mihomo-linux-mipsel-softfloat-vX.Y.Z` — the binary;
- `mihomo-linux-mipsel-softfloat-vX.Y.Z.sha256` — checksum to verify the download.

Verify a download:

```sh
sha256sum --check mihomo-linux-mipsel-softfloat-vX.Y.Z.sha256
```

Current releases: [Releases](https://github.com/saymer-alt/mihomo-auto-build/releases).

## Using a built binary

1. Download the binary and its `.sha256` from the release matching your target Mihomo version, and verify the checksum as shown above.
2. Deploy it the way your Mihomo setup expects (replace the existing binary, keep ownership/executable bits).
3. Confirm the running version: `mihomo -v`.

On Keenetic routers with Entware, the binary path and service management depend on your installation method — see the related projects below before replacing anything.

## Scope and limitations

- **MIPSel softfloat only.** Other architectures are covered by official [MetaCubeX/mihomo releases](https://github.com/MetaCubeX/mihomo/releases) or the Entware package feed in [`saymer-alt/entware-go`](https://github.com/saymer-alt/entware-go) (release `latest`).
- Builds are produced by CI from unmodified upstream source tags; no patches are applied.
- Release publication is deliberately conservative: partial or failed uploads are replaced only after validation, never blindly (`--clobber` is not used).

## Development

- `scripts/release_assets.py` — publication state machine (plan/publish) used by the build workflow.
- `tests/test_release_assets.py`, `tests/test_starter_recovery.py` — offline tests for the publication logic.
- `.github/workflows/test-release-readiness.yml` — runs the tests on push.

Run the tests locally (same command as CI):

```sh
python3 -m unittest discover -s tests -p "test_*.py"
```

## Related projects

- [`saymer-alt/keenetic-auto-setup`](https://github.com/saymer-alt/keenetic-auto-setup) — automated Mihomo deployment on Keenetic routers with Entware.
- [`saymer-alt/entware-go`](https://github.com/saymer-alt/entware-go) — Entware package feed shipping Mihomo `.ipk` packages for several architectures.
