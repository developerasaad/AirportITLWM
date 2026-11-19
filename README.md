# AirportItlwm — AX211 / Sequoia Debug

A single-target fork of [laobamac/itlwm](https://github.com/laobamac/itlwm)
providing the native macOS AirportItlwm kernel extension for exactly one
configuration:

| Field | Value |
|---|---|
| Computer | MSI Modern 14 C12MO |
| Wireless adapter | Intel Wi-Fi 6E AX211 160 MHz |
| Operating system | macOS Sequoia 15.8.2 (Darwin 24.x) |
| Architecture | x86_64 |
| Driver | `AirportItlwm.kext` |
| Configuration | Debug only |
| Integration | Native macOS Wi-Fi (Airport / IO80211 / Skywalk / WCL) |

No Sonoma, Tahoe, Ventura, HeliPort, Ethernet-emulation, or non-AX211 Intel
adapter support is maintained.

## Source foundation

Upstream: `https://github.com/laobamac/itlwm`
Baseline commit: `4ea299cf3b8599d91c55f5eab477b1d03b6eae82`
("Merge pull request #36 from mingww64/fix/wpa3-transition-and-amsdu")

The previous Dell G3 3579 / Intel AC 9462 experiment that physically failed
on its target is preserved as the recoverable reference
`archive/dell-ac9462-v2.5.0-alpha` (commit `1dd6382`, also reachable in
`main` history). It is not under active development.

## Build

Manual GitHub Actions workflow only:
**Actions → "Build AX211 Sequoia Debug" → Run workflow** on `main`.
Runner: `macos-15-intel`. MacKernelSDK is pinned at
`3f750085caa17ec3a7880f11c11bf4f48cd6a164`.
Inputs: `publish_release` (default `true`) publishes the verified build
into the rolling release by replacing its assets;
`release_name` (default `v2.5.0-alpha`) selects the target release by
name — it must already exist, because CI never creates releases or tags.

Local build (Xcode + Python 3, MacKernelSDK checked out in `MacKernelSDK/`):

```sh
xcodebuild -project itlwm.xcodeproj -scheme AirportItlwm-Sequoia \
  -configuration Debug ARCHS=x86_64 CODE_SIGNING_ALLOWED=NO \
  SYMROOT="$PWD/build/products" OBJROOT="$PWD/build/obj" build
```

Output: `build/products/Debug/Sequoia/AirportItlwm.kext`.

## Releases

Standalone release publishing — no tag-based releases. Releases are
never created from tags and never triggered by tag events; the manual
workflow dispatch is the only release path, and CI never creates tags,
releases, or refs. Each release is a single fixed object whose assets
are replaced in place. Exactly two releases are kept:

| Release | Role | Assets |
|---|---|---|
| `v2.5.0-alpha` (prerelease) | **Rolling current build** — assets replaced in place by every successful dispatch build | newest `AX211-Sequoia-Debug` zip + sha256s only |
| `v2.4.0-ax211-reduced` (prerelease) | Frozen historical release (reduced 2.4.0 line, hardware-handoff notes) | `207c20a` build (asset filename keeps the original `f588ecd`) |

The publish job resolves the rolling release by name via the releases
API (release-ID based, no tag involvement), deletes prior
`AirportItlwm-*AX211-Sequoia-Debug-*` assets, and uploads the fresh
build, so the release always ships exactly the newest verified binary.
The same-named lightweight tags exist only as fixed anchors required by
GitHub's release model; they never move and nothing is ever built or
published from them. Superseded releases/tags (`v2.4.0-baseline-ax211`,
`dell-ac9462-v2.5.0-alpha-final`, `ax211-baseline-validated`) were
removed on 2026-11-19.

History note (2026-11-19): the entire repository history was
re-attributed to the repository owner (single-contributor
normalization); all historical commit SHAs changed accordingly.

## Status

- **Baseline:** clean, unmodified laobamac upstream Sequoia Debug build,
  hardware-validated on the MSI (AX211 / Sequoia 15.8.2). Preserved on
  branch `baseline-validated` (commit `346091b`).
- **Reduced build:** AX211-only source reduction applied (see below). CI-verified
  and independently re-verified. **NOT yet hardware-verified** on the MSI.
- **Firmware API 89:** the active line (`main`, mirrored to branch
  `ax211-api89-modernization`). Replaces the embedded API 68 set with the exact
  API 89 build validated on the target under Ubuntu 26.10
  (`iwlwifi-so-a0-gf-a0-89.ucode`, version 89.d2579d43.0, plus its PNVM),
  ports every reshaped command (scan v17, PHY context v4 + RLC, session
  protection v2, TLC v4, BAID allocation, TVQM v3 queue config, segmented
  PNVM), adds a command-ABI registry that rejects unsupported firmware, and
  lands the audit's P0/P1 driver fixes (roaming un-latch, idle scan park,
  association retry, BA leaks, watchdog gating, EAPOL length guard, and
  others). Record: `research/ax211-api89/FIRMWARE-89.md` (provenance + ABI
  delta) and `research/ax211-api89/STATUS.md` (per-workstream status and the
  remaining-work register, incl. WPA3-SAE and 6 GHz). **CI-verified; NOT yet
  hardware-verified.**
- **Deferred (Tier 2):** IWX-internal specialization (Qu/AX200/9000 device-table
  entries + their iwlwifi-* firmware) is deferred pending the MSI's exact PCI
  device+subdevice identity (the device->adapter mapping is subdevice-dependent).

### Source reduction (Tier 1)

Removed from the active source tree (not merely excluded from compilation):

- `itlwm/hal_iwn/` (4 files) -- legacy 4965/6000 family
- `itlwm/hal_iwm/` (21 files) -- 8000/9000 family (AC 9260/9462/9560)
- standalone itlwm kext (HeliPort path): `itlwm.cpp`, `itlwm.hpp`, `pm.cpp`,
  `ItlNetworkUserClient.cpp/.hpp`, `itlwm/Info.plist`
- `include/Airport/macOS26/` (9 Tahoe headers)
- `AirportItlwm/AirportItlwm-Sonoma-Info.plist`, `AirportItlwm-Monterey-Info.plist`
- 3 schemes (`itlwm`, `AirportItlwm (all)`, `AirportItlwm-Tahoe`)
- 10 Xcode native targets (itlwm + Big Sur/Mojave/High Sierra/Monterey/Catalina/
  Ventura/Sonoma14.0/Sonoma14.4/Tahoe) + their build phases, config lists,
  configs, and non-shared product refs
- 20 firmware files (8 `iwm-*` + 12 `iwn-*`)
- `IOPCIMatch` pruned from ~80 PCI IDs to the 19 iwx device IDs (all iwm/iwn
  PCI IDs removed) in every Sequoia-baked plist

Minimal AirportItlwm edits (behavior-preserving): `probe()` dispatch reduced to
the single `ItlIwx` branch; `ItlIwm.hpp`/`ItlIwn.hpp` includes removed; macOS26
`FaultReporter` conditional simplified to macOS15; shared `IWM_MIN_DBM` constant
(-100) relocated to `if_iwxreg.h` (same value as `IWX_MIN_DBM`).

### Reduction measurements (before -> after)

| Metric | Baseline | Reduced | Delta |
|---|---|---|---|
| Source files (.cpp/.hpp/.h/.c) | 215 | 176 | -18.1% |
| Source lines | 124,331 | 83,830 | -32.6% |
| Compiled translation units (Sequoia) | 75 | 57 | -24.0% |
| Firmware files | 35 | 15 | -57.1% |
| Firmware bytes | 35.0 MB | 16.7 MB | -52.3% |
| Binary size | 16,262,720 B (15.51 MB) | 7,622,312 B (7.27 MB) | -53.1% |
| project.pbxproj lines | 4,448 | 1,999 | -55.1% |
| Hardware backends | 3 (iwn+iwm+iwx) | 1 (iwx) | -2 |
| Xcode native targets | 11 | 1 (+fw_gen aggregate) | -10 |
| Xcode schemes | 4 | 1 | -3 |

### Reduced build record

| Field | Value |
|---|---|
| Source commit | `207c20a` (reduced-line HEAD at build time) |
| Reduction commits | `f8d6c8c` (reduction) + `0548467`/`f88ecab`/`207c20a` (build fixes) |
| Workflow run | https://github.com/developerasaad/AirportITLWM/actions/runs/44145096042 |
| Runner | `macos-15-intel` |
| Configuration | Sequoia / Debug / x86_64 |
| Kext | `AirportItlwm.kext` (com.zxystd.AirportItlwm, version 2.4.0) |
| Binary size | 7,622,312 bytes |
| Binary SHA-256 | `30a3ce590b8c137faa0e7f593733bacb15dd1c1c2e5f98773b4f6b350a6b674a` |
| Artifact SHA-256 | `da628dc5a26a733e6591cc69d85e9547de4a88ff291d066e48bb42b681e0f4fa` |
| AX211 PCI match | `0x51F08086 0x51F18086 0x54F08086 0x7E408086 0x7F708086` |
| Sequoia libs | IOSkywalkFamily 1.0, corecapture 1.0.0, IO80211Family 1.5.0 |

Hardware-test handoff and rollback procedure are published with the prerelease
tagged `v2.4.0-ax211-reduced`.

## License

Upstream `LICENSE` (BSD-2-Clause) and `iwlwifi-firmware-license` are retained
unchanged. Copyright and source provenance are preserved.


## Forensic audit (2026-11-18)

A source-level forensic audit of this reduced tree is preserved in
[`research/ax211-audit/`](research/ax211-audit/DOSSIER.md) - 152 findings
plus an 18-finding cross-platform correspondence analysis. Remote runtime
evidence could not be collected in that environment; a sanitized,
owner-runnable diagnostic kit for runtime confirmation is in
[`research/ax211-audit/tools/`](research/ax211-audit/tools/README.md).
No driver source was modified by the audit.
