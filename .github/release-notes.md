**AirportItlwm for the Dell G3 3579 (Intel Wireless-AC 9462) — instrumented development build**
**All builds x86_64. Source commit and build identity: appended below by CI.**

## Which build to install
| Your macOS | Install |
|---|---|
| 14.0 – 14.3 | `AirportItlwm-Sonoma14.0-v2.5.0-...-alpha-<commit>.zip` |
| 14.4 – 14.x | `AirportItlwm-Sonoma14.4-v2.5.0-...-alpha-<commit>.zip` |
| 15.2 – 15.x (incl. 15.8.2) | `AirportItlwm-Sequoia-v2.5.0-...-alpha-<commit>.zip` |

Use **RELEASE** for daily use; **DEBUG** only when investigating a problem
(verbose driver logging). SHA-256 checksums are alongside each zip.

Firmware for the AC 9462 (`iwm-9000-46`, CNVi 9000-series) is embedded; no
external firmware files are required.

## What this build is
`v2.4.0-alpha` **failed physical validation** on the target machine
(see issues #3–#6 for the post-mortem). The log archive
`airportitlwm-logs-20261117-201349.zip` showed joins taking ~25 s
against airportd's ~10 s window, directed scans timing out at −3905,
network lists vanishing after cache clears, and a spontaneous link drop
~50 s after association. This `v2.5.0-alpha` build is the reassessed,
reengineered implementation with join/scan diagnostics for physical
testing.

## What changed (root causes from the physical evidence)
1. **Join fast path (wrong-password / retry loop).** `setASSOCIATE`
   previously only *recorded* the desired network; the association waited
   for the next full-band firmware scan (~25 s) to pick the target — every
   airportd join attempt therefore timed out and macOS re-asked for the
   password. The driver now associates directly to the cached scan target
   (macOS scans right before the user picks a network): sub-second joins,
   and retries supersede the in-flight attempt without restarting a scan.
   If the radio is mid-scan, the join aborts the scan and completes via
   the standard state machine.
2. **Directed scans (network list churn / missing networks).** Apple80211
   scan requests carry a channel subset and dwell; the driver ignored
   them and swept the entire band (~25 s), so airportd's ~10 s
   per-request window always expired (−3905 Timeout, canceled requests,
   stale lists). Restricted directed scans now complete in ~1–5 s with
   the requested channels and dwell.
3. **Stable scan results (disappearing networks).** Enumeration walked a
   live tree cursor that dangles when nodes are freed between macOS polls
   (cache clears, background sweeps) — garbage entries and use-after-free
   reads. Results are now served from a snapshot converted under the
   command gate and rebuilt on scan completion, cache serves, and cache
   clears.
4. **State reporting.** `getSSID`/`getBSSID`/`getCHANNEL` returned errors
   when disassociated (airportd −3903 spam) and the SSID getter reported
   the *desired* ESSID through `strlen()`. They now return success with
   empty payloads when disassociated and report the actual associated
   BSS's ESSID by length.
5. **Network switching.** Switching networks without a prior DISASSOCIATE
   no longer forces a full-band rescan; the driver deauths and fast-joins
   the new cached target. `ROAM_PROFILE` get/set is implemented
   (airportd's per-band profile pushes previously failed on every
   association).
6. **Security.** PTK/GTK/PMK key hexdumps and full EAPOL frame dumps
   (which carry key material in the 4-way handshake) are removed from the
   kernel log; key operations log metadata only.

## New diagnostics for physical testing
The driver now logs (kernel log, captured by
`log show --predicate 'eventMessage CONTAINS "itlwm"'`):
join fast-path decisions (`join: fast-path …`, `join: no cached BSS …`),
auth/assoc response status codes (`join-diag: …`),
join timeouts (`join-timeout: …`),
missed-beacon counts vs threshold and probe timeouts (`link-diag: …`,
`link-loss: …`),
scan requests/restrictions/completions (`scan(req): …`, `scan(end): …`,
`scan(umac/lmac/iwx): …`),
and deauth reasons. These distinguish: rejected scan, incomplete scan,
empty scan result, failed authentication, association timeout,
security-handshake failure, key-installation failure, invalid state
transition, cancellation/supersession, firmware-command failure, link
loss after association, and native reporting inconsistencies.

## Specific behaviors to test (in order)
1. **Join latency.** Join a known network from the Wi-Fi menu — the
   connection should complete in ~1–3 s, first try. Then join a second
   network, then switch back — each switch should be fast and stable.
2. **Retry with corrected password.** Join with a deliberately wrong
   password, then retry with the correct one — the retry must connect
   without repeating the spinner loop.
3. **Network list stability.** Open the Wi-Fi menu and the System
   Settings Wi-Fi panel side by side; both should agree, stay populated,
   and refresh within ~5 s after a cache clear. No disappearing networks.
4. **Reconnection after link loss.** With the machine associated, power
   the AP off for ~15 s, then back on — the client should reassociate
   within ~10–15 s without manual intervention. Repeat with the machine
   ~1 m from the AP (RSSI −40 to −50).
5. **Long-session stability.** Keep the machine associated for ≥ 30 min
   with traffic; watch for spontaneous drops and check the kernel log for
   `link-diag:`/`link-loss:` lines if any occur.
6. **Sleep/wake.** Sleep and wake the machine — the link should return
   within a few seconds.

## Collecting diagnostics for a report
Run `scripts/collect-diagnostics.sh` (in the repo) after reproducing a
failure, or manually capture ~120 s of driver log with the command above
plus a note of the time. The WifiShadow-style monitoring used for the
last capture is also fine. Please attach logs to the corresponding issue.

**This is a development pre-release. It is CI-verified (build, package,
source invariants) but NOT hardware-verified. Do not consider it
stable.**
