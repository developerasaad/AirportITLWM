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

- **Baseline (this commit):** clean, unmodified laobamac upstream Sequoia
  Debug build. CI-verified (architecture, bundle identity, Sequoia Skywalk /
  corecapture linkage, AX211 PCI device matching, embedded Gen3 firmware).
- **Hardware validation:** PENDING on the MSI target. Not yet physically
  tested. Do not assume Wi-Fi works until the baseline is confirmed on the
  MSI.
- **Source reduction:** NOT STARTED. Per project policy, destructive pruning
  is blocked until the upstream baseline is hardware-validated on the MSI.

## License

Upstream `LICENSE` (BSD-2-Clause) and `iwlwifi-firmware-license` are retained
unchanged. Copyright and source provenance are preserved.
