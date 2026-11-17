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
Baseline commit: `7204c69d1bfa7f5cc0f7864e08fb03e55d0ec29e`
("Merge pull request #36 from mingww64/fix/wpa3-transition-and-amsdu")

The previous Dell G3 3579 / Intel AC 9462 experiment that physically failed
on its target is preserved as the recoverable reference
`archive/dell-ac9462-v2.5.0-alpha` (tag `dell-ac9462-v2.5.0-alpha-final`,
commit `812ea1c`). It is not under active development.

## Build

Manual GitHub Actions workflow only:
**Actions → "Build AX211 Sequoia Debug" → Run workflow** on `main`.
Runner: `macos-15-intel`. MacKernelSDK is pinned at
`3f750085caa17ec3a7880f11c11bf4f48cd6a164`.

Local build (Xcode + Python 3, MacKernelSDK checked out in `MacKernelSDK/`):

```sh
xcodebuild -project itlwm.xcodeproj -scheme AirportItlwm-Sequoia \
  -configuration Debug ARCHS=x86_64 CODE_SIGNING_ALLOWED=NO \
  SYMROOT="$PWD/build/products" OBJROOT="$PWD/build/obj" build
```

Output: `build/products/Debug/Sequoia/AirportItlwm.kext`.

## Status

- **Baseline:** clean, unmodified laobamac upstream Sequoia Debug build.
  CI-verified and independently re-verified (architecture, bundle identity,
  Sequoia Skywalk / corecapture linkage, AX211 PCI device matching, embedded
  Gen3 firmware, SHA-256).
- **Hardware validation:** PENDING on the MSI target. Not yet physically
  tested. Do not assume Wi-Fi works until the baseline is confirmed on the MSI.
- **Source reduction:** NOT STARTED. Per project policy, destructive pruning
  is blocked until the upstream baseline is hardware-validated on the MSI.

### Baseline build record

| Field | Value |
|---|---|
| Source commit | `aa193163c2a8c36fbaa86fea2113e7f74e4fdf96` |
| Upstream baseline | laobamac/itlwm `7204c69d1bfa7f5cc0f7864e08fb03e55d0ec29e` |
| Workflow run | https://github.com/developerasaad/AirportITLWM/actions/runs/44135504957 |
| Runner | `macos-15-intel` |
| Configuration | Sequoia / Debug / x86_64 |
| Kext | `AirportItlwm.kext` (com.zxystd.AirportItlwm, version 2.4.0) |
| Binary size | 16,262,720 bytes |
| Binary SHA-256 | `aafb5f8e1a9b077118a7796092a57c3d849f2e7e4b7a7dcf0185c4eb13110214` |
| Artifact SHA-256 | `dd32af74c199f98ed7cc0c9fc950f548138631048740226492857984c850d90b` |
| AX211 PCI match | `0x51F08086 0x51F18086 0x54F08086 0x7E408086 0x7F708086` |
| Sequoia libs | IOSkywalkFamily 1.0, corecapture 1.0.0, IO80211Family 1.5.0 |

Hardware-test handoff and rollback procedure are published with the
prerelease tagged `v2.4.0-baseline-ax211`.

## License

Upstream `LICENSE` (BSD-2-Clause) and `iwlwifi-firmware-license` are retained
unchanged. Copyright and source provenance are preserved.
