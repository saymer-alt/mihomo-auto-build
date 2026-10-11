# mihomo-auto-build

Automated builds of [Mihomo](https://github.com/MetaCubeX/mihomo) (Clash Meta) for **MIPSel (softfloat)** routers and embedded Linux devices, produced and published by GitHub Actions.

Upstream Mihomo publishes official binaries for many platforms, but not for `mipsle / GOMIPS=softfloat` — the combination required by MT7621-class MIPSel routers. This repository builds that target from source on every upstream release.

## What it does

A scheduled workflow ([`build-mihomo-mipsel.yml`](.github/workflows/build-mihomo-mipsel.yml), daily at 03:00 UTC, manual dispatch enabled):

1. Reads the latest upstream Mihomo release (` vX.Y.Z`, strict semver check).
2. Inspects the existing publication state and builds **only what is missing or invalid** — a healthy released binary is never overwritten (`scripts/release_assets.py` publication state machine).
3. Builds from the upstream source tag:
   `CGO_ENABLED=0 GOOS=linux GOARCH=mipsle GOMIPS=softfloat`, with `-trimpath -ldflags "-s -w"` and a stamped version string.
4. Publishes release assets on a `mipsel-vX.Y.Z` tag, verifies SHA-256 digests, and ensures the matching upstream Mihomo GPL-3.0 LICENSE is attached. The notice step never replaces a healthy binary or checksum.

## Releases and assets

Each upstream version gets a release tagged `mipsel-vX.Y.Z` with:

- `mihomo-linux-mipsel-softfloat-vX.Y.Z` — the binary;
- `mihomo-linux-mipsel-softfloat-vX.Y.Z.sha256` — checksum to verify the download.
- `mihomo-linux-mipsel-softfloat-vX.Y.Z.LICENSE` — exact upstream Mihomo GPL-3.0 license text retrieved from the matching `vX.Y.Z` source tag (for releases published by the updated workflow).
- `THIRD_PARTY_LICENSES-vX.Y.Z.txt` — dependency audit summary with licensing indicators; not a legal compliance certificate.
- `THIRD_PARTY_NOTICES-vX.Y.Z.txt` — full collected upstream and dependency notice texts, generated from the exact built binary's Go module information.

Verify a download:

```sh
sha256sum --check mihomo-linux-mipsel-softfloat-vX.Y.Z.sha256
```

Current releases: [Releases](https://github.com/saymer-alt/mihomo-auto-build/releases). **Source availability:** [version-specific upstream source downloads, build scripts and GPLv3 §6(d) review checklist](SOURCE-AVAILABILITY.md). For a new version, the release description now includes pinned source and build links; older release pages still need an explicit audit.

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
4. Back up the currently working binary before replacing it, so a rollback is always possible. Note where that binary lives — you will need the same path (or the same `PATH` lookup) for verification in step 6.
5. **Stop the service first**, replace the binary (keep ownership/executable bits), then start the service again. The exact commands depend on your setup — for example, systemd uses `systemctl stop mihomo` / `systemctl start mihomo`, while an Entware install from [keenetic-auto-setup](https://github.com/saymer-alt/keenetic-auto-setup) uses `/opt/etc/init.d/S99mihomo stop` / `start`. Do not replace a binary while the service is running: the running process keeps the old file mapped, and a half-replaced state is easy to misdiagnose. This README does not assume any specific install path — use the path your own service configuration points to.
6. Verify the version of the **actually running process** after the restart:

   ```sh
   mihomo -v
   ```

   This prints the version of the binary found via `PATH` (or run it with the explicit path from step 4/5). The most reliable check of the running daemon is the controller API `GET /version` — it is what dashboards like MetaCubeXD display. If the check still reports the old version, the service is executing a different file than the one you replaced — find the binary path from your service configuration and repeat the replacement on that file.

7. **Rollback.** If Mihomo does not start after the replacement — or the version check shows anything other than the expected release — restore the backup from step 4 to the same path, restart the service, and re-verify. Check the release notes for known issues before retrying the new binary. Do not leave the service stopped while investigating.

## Scope and limitations

- **MIPSel softfloat only.** Other architectures are covered by official [MetaCubeX/mihomo releases](https://github.com/MetaCubeX/mihomo/releases) or the Entware package feed in [`saymer-alt/entware-go`](https://github.com/saymer-alt/entware-go) (release `latest`).
- Builds are produced by CI from unmodified upstream source tags; no patches are applied. New releases link to the exact upstream source tag and immutable build-script revision. That pointer alone is **not** an audited complete corresponding-source bundle.
- Release publication is deliberately conservative: partial or failed uploads are replaced only after validation, never blindly (`--clobber` is not used).

## Development

- `scripts/release_assets.py` — publication state machine (plan/publish) used by the build workflow.
- `scripts/release_license.py` — independent, fail-closed tagged upstream GPL-3.0 license asset publication/verification.
- `scripts/collect_upstream_licenses.py` and `scripts/release_notices.py` — per-version dependency license collection and verification of the two notice assets; unknown or conflicting notices stop publication.
- `tests/test_release_assets.py`, `tests/test_starter_recovery.py`, `tests/test_release_license.py`, `tests/test_release_notices.py`, `tests/test_third_party_notices.py`, `tests/test_source_availability.py` — offline tests for publication, recovery, licensing, notice integrity and future release source pointers.
- `.github/workflows/test-release-readiness.yml` — runs the tests on push.

Run the tests locally (same command as CI):

```sh
python3 -m unittest discover -s tests -p "test_*.py"
```

## Licensing and attribution

This repository builds upstream [MetaCubeX/mihomo](https://github.com/MetaCubeX/mihomo) from tagged source. **Upstream Mihomo is licensed under GNU GPL-3.0**, as verified for the published `v1.19.24`–`v1.19.32` tags; see the exact tagged [upstream LICENSE](https://github.com/MetaCubeX/mihomo/blob/v1.19.32/LICENSE) and [UPSTREAM_NOTICE.md](UPSTREAM_NOTICE.md). **The original builder scripts and workflows authored by saymer-alt are separately licensed under MIT** (© 2026 saymer-alt; [LICENSE](LICENSE)). The release workflow is designed to attach the tagged upstream GPL-3.0 text and a per-version third-party license summary and full collected notice texts. Automatic classification is a provenance aid, **not proof of license compatibility or fulfillment of every GPL source-distribution obligation**. See [LICENSING.md](LICENSING.md) and [Issue #8](https://github.com/saymer-alt/mihomo-auto-build/issues/8).

## Historical release notice backfill (completed 2026-10-10)

All eight historical releases (`v1.19.24`–`v1.19.31`) now have the same **five release assets**
as `v1.19.32`: original MIPSel binary, `.sha256` sidecar, exact tagged upstream GPL-3.0
`.LICENSE`, version-specific `THIRD_PARTY_LICENSES` and full `THIRD_PARTY_NOTICES`.
The missing four assets per historical version (32 total) were added **without replacing any
published binary**. The owner-run [read-only audit](https://github.com/saymer-alt/mihomo-auto-build/actions/runs/38088679082)
and per-version manual `plan → publish` runs are recorded in
[Issue #8](https://github.com/saymer-alt/mihomo-auto-build/issues/8#issuecomment-6102988561).

The [historical backfill workflow](.github/workflows/historical-license-backfill.yml)
remains **manual-only**, defaults to read-only `mode=plan` and refuses to rebuild/replace
an existing binary. It should not be run in `publish` mode routinely against already
complete releases. For future recovery, inspect existing asset IDs/digests, run `plan` first,
and use `publish` only for explicitly approved, verified missing notice assets.

**Limitations:** GitHub Actions PASS and the five assets do **not** prove Complete Corresponding
Source availability or resolve GPL/LGPL/MPL compliance and code-linkage questions.
The outstanding review remains tracked in [Issue #8](https://github.com/saymer-alt/mihomo-auto-build/issues/8).

## Related projects

- [`saymer-alt/keenetic-auto-setup`](https://github.com/saymer-alt/keenetic-auto-setup) — automated Mihomo deployment on Keenetic routers with Entware.
- [`saymer-alt/entware-go`](https://github.com/saymer-alt/entware-go) — Entware package feed shipping Mihomo `.ipk` packages for several architectures.
