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

## Is my device supported?

This build targets **MIPS little-endian with soft-float** (`GOARCH=mipsle`, `GOMIPS=softfloat`) — the combination required by MT7621-class MIPSel routers. If your device is AArch64/ARM64 or another architecture, these binaries are **not** for it: use the official [MetaCubeX/mihomo releases](https://github.com/MetaCubeX/mihomo/releases) or the [`saymer-alt/entware-go`](https://github.com/saymer-alt/entware-go) package feed instead. When unsure about your hardware, check the vendor specification for the SoC first.

## Using a built binary

1. Open [Releases](https://github.com/saymer-alt/mihomo-auto-build/releases) and pick the release matching your target Mihomo version (tags look like `mipsel-v1.19.32`).
2. Download **both** files: the binary and its `.sha256`.
3. Verify the checksum (run where you downloaded the files):

   ```sh
   sha256sum --check mihomo-linux-mipsel-softfloat-vX.Y.Z.sha256
   # expected output:
   # mihomo-linux-mipsel-softfloat-vX.Y.Z: OK
   ```

   If the check fails, do not use the file — re-download and compare release notes.
4. Back up the currently working binary before replacing it, so a rollback is always possible.
5. Replace the binary with correct ownership/executable bits, then restart your Mihomo service. The exact commands depend on your setup — for example, systemd uses `systemctl stop mihomo` / `systemctl start mihomo`, while an Entware install from [keenetic-auto-setup](https://github.com/saymer-alt/keenetic-auto-setup) uses `/opt/etc/init.d/S99mihomo stop` / `start`.
6. Confirm the running version:

   ```sh
   mihomo -v
   ```

If Mihomo does not start after the replacement, restore the backup from step 4 and restart the service again — then check the release notes for known issues before retrying.

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
