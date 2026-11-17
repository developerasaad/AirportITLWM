# AirportItlwm — Dell G3 3579 (Intel Wireless-AC 9462)

A hardware-focused engineering fork of **AirportItlwm.kext** — the native macOS
Wi-Fi kernel extension for Intel wireless adapters — refined for the
**Dell G3 3579** laptop with the **Intel Wireless-AC 9462** (CNVi, 9000-series,
802.11ac / Wi-Fi 5, 1×1 radio) on **x86_64**.

## Supported systems

| Build | macOS range | Notes |
|---|---|---|
| `AirportItlwm-Sonoma14.0` | 14.0 – 14.3 | Apple changed private IO80211 ABI in 14.4 |
| `AirportItlwm-Sonoma14.4` | 14.4 – 14.x | |
| `AirportItlwm-Sequoia` | 15.2 – 15.x (Darwin 24.2.0+) | 15.0/15.1 have no native support in any known source |

All builds are **x86_64 only**. The Sequoia build uses the WCL native Wi-Fi
stack (IO80211Family V2 + IOSkywalk + AppleVTD bounce-buffer DMA).

## Hardware path (this machine)

- PCI IDs `8086:42a4 / 8086:00a0 / 8086:00a4 / 8086:02a0 / 8086:40a4`
- Driver backend: `hal_iwm` (OpenBSD iwm port), `IWM_DEVICE_FAMILY_9000`
- Firmware: `iwm-9000-46` (Intel `iwlwifi 9000-pu-b0-jf-b0-46`), embedded
  (zlib-compressed) in the kext binary — no external firmware files needed.

## Installation

1. Pick the build matching your exact macOS version (see table above).
2. Replace any existing `AirportItlwm.kext` in `EFI/OC/Kexts/` (or
   `/Library/Extensions` for legacy boot loaders).
3. Update your boot-loader kext list/Kernel cache if needed (OpenCore:
   `Kernel → Add` entry must point at the new file; Legacy Kexts: rebuild
   cache with `sudo kmutil install --update-all`).
4. Reboot.

**Debug vs Release:** Debug builds contain verbose diagnostic logging
(`XYLog`) for investigating issues. Use Release for daily use.

## Rollback

Restore your previous `AirportItlwm.kext` (keep a copy before installing) and
rebuild the kernel cache. The driver does not modify your EFI beyond the kext
file itself.

## Collecting diagnostics

If a build misbehaves, run on the target machine:

```sh
bash scripts/collect-diagnostics.sh [seconds_of_recent_logs]
```

It writes a tarball to your Desktop with driver-relevant logs, kext load
state, and sleep/wake timeline — attach it to the matching GitHub issue.

## Build

CI (GitHub Actions, `macos-15-intel` runner) builds and verifies every push:
Sonoma14.0/Sonoma14.4/Sequoia × Debug/Release, checking architecture, bundle
identity, OSBundleLibraries, embedded firmware inventory, and publishing
SHA-256-verified pre-release zips.

Local build requires Xcode and MacKernelSDK at commit `3f75008`:

```sh
xcodebuild -project itlwm.xcodeproj -scheme AirportItlwm-Sequoia \
  -configuration Release ARCHS=x86_64 CODE_SIGNING_ALLOWED=NO build
```

## Provenance and licensing

- Baseline: [laobamac/itlwm](https://github.com/laobamac/itlwm) main @ `7204c69`
  — a strict superset of [OpenIntelWireless/itlwm](https://github.com/OpenIntelWireless/itlwm)
  master @ `53c51c2` (+47 commits) adding native Sequoia 15.2+ support and
  correctness fixes. Full upstream git history is preserved in this repository.
- Upstream credits and license terms apply (see `LICENSE`,
  `iwlwifi-firmware-license/`). Based on the OpenBSD `iwm` driver
  (OpenBSD), Linux `iwlwifi` references, and the original AirportItlwm
  work by zxystd and OpenIntelWireless contributors; MacKernelSDK by
  acidanthera; WCL/Sequoia+Tahoe support by laobamac.
- Intel firmware is redistributed under the terms documented in
  `iwlwifi-firmware-license/`.

## Status

Engineering is active on this repository. **All builds are CI-verified only —
no hardware validation has been performed yet.** Defect work is tracked in
issues #3–#6; overall state in issue #7. Development pre-releases carry the
`-alpha-<commit>` suffix; nothing is marked stable without physical
confirmation on the target machine.
