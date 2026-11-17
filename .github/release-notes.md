**AirportItlwm for the Dell G3 3579 (Intel Wireless-AC 9462) — development build**
**All builds x86_64. Source commit and build identity: appended below by CI.**

## Which build to install
| Your macOS | Install |
|---|---|
| 14.0 – 14.3 | `AirportItlwm-Sonoma14.0-v2.4.0-...-alpha-<commit>.zip` |
| 14.4 – 14.x | `AirportItlwm-Sonoma14.4-v2.4.0-...-alpha-<commit>.zip` |
| 15.2 – 15.x (incl. 15.8.2) | `AirportItlwm-Sequoia-v2.4.0-...-alpha-<commit>.zip` |

Use **RELEASE** for daily use; **DEBUG** only when investigating a problem
(verbose driver logging). SHA-256 checksums are alongside each zip.

Firmware for the AC 9462 (`iwm-9000-46`, CNVi 9000-series) is embedded; no
external firmware files are required.

## What changed vs the baseline (laobamac/itlwm @ 7204c69)
Four macOS-visible defect classes were corrected (details in issues #3-#6):
1. **Wrong-password reports on valid credentials** — join retries are no
   longer silently swallowed mid-attempt, and the PMK copy no longer
   carries stale bytes from a previous network.
2. **Network list refreshing during connection** — macOS now receives the
   real firmware scan completion (once per request) instead of a fake
   100 ms timer that raced the actual sweep.
3. **"No networks available"** — scan-result enumeration cursor is
   initialized and reset on every cache invalidation; stale-cursor EINVAL
   rejections removed; scan results now carry correct rates.
4. **Unstable switching/reconnection** — DISASSOCIATE cancels in-flight
   joins; ASSOCIATE properly leaves the current BSS when switching
   networks; firmware station-context flag no longer set on command
   transport failure.

Plus diagnostic logging for association supersession, skipped background
scans, and time-event failures; a safe read-only diagnostic collection
script (`scripts/collect-diagnostics.sh`).

## Specific behaviors to test (in order)
1. **Defect A:** join a WPA2-Personal network with a deliberately wrong
   password, then immediately retry with the correct one in the same
   attempt window — the retry must connect. Then change the AP password
   and reconnect.
2. **Defect C:** open the Wi-Fi list right after boot, right after enabling
   Wi-Fi, and right after a failed connection — networks must appear
   within seconds; the list must never go permanently empty with APs nearby.
3. **Defect B:** start a connection while the Wi-Fi list is open — the list
   should not visibly refresh/restart mid-attempt.
4. **Defect D:** switch rapidly between two networks; reconnect after an AP
   reboot, after sleep/wake, and after toggling Wi-Fi off/on.
5. General: throughput (2.4+5 GHz), long-session stability, sleep/wake
   reliability.

## Results needed
For any failure: run `bash scripts/collect-diagnostics.sh` on the machine and
attach the produced tarball to the matching issue (#3-#6), noting the
build (Sonoma14.0/14.4/Sequoia, Debug/Release) and macOS version.

## Known risks / limitations
- No hardware validation has occurred yet — this is exactly what this
  pre-release is for.
- Sequoia 15.0/15.1 are NOT supported (Apple ABI change); requires 15.2+.
- WPA3-only and mandatory-PMF networks remain unsupported (inherited).
- Sonoma scan enumeration still walks the live node cache (bounded by the
  cursor-reset fixes); a fully snapshot-based design is deferred pending
  physical evidence (issue #5).

## Rollback
Keep your previous AirportItlwm.kext; restore it in EFI/OC/Kexts (or
/Library/Extensions) and rebuild the kernel cache. Nothing else is modified
by this driver.

**Hardware validation is required before daily use. Nothing here is marked
stable — stable requires physical confirmation on the target machine.**
