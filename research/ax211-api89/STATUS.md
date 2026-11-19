# AX211 API-89 Modernization — Status and Compatibility Matrix

Branch: `ax211-api89-modernization` (mirrors `main`).
Baseline start: `40fb4c2` (audit head, tag `v2.4.0-ax211-reduced` parent lineage;
hardware-validated reference: `ax211-baseline-validated` @ `aa19316`).

Classification follows the mission's completion criteria:
[1] implemented and locally verified (CI build + verification evidence),
[2] implemented, awaiting physical validation on the MSI,
[3] not implemented, with the remaining work specified.

## Firmware

| Item | Status | Evidence |
|---|---|---|
| API 89 firmware embedded (89.d2579d43.0, exact Ubuntu 26.10 build) | [1] | CI run 44488552927: binary_size=1788744, `iwlwifi-so-a0-gf-a0-89 -> embedded`, artifact sha256 `ba912090...` |
| PNVM (sha256 776606c7...) embedded, SKU-matched parse | [1] | CI fw-strings check; parse code logs SKU match at runtime |
| Segmented PNVM DRAM (capa FRAGMENTED_PNVM_IMG) | [2] | Implemented per Linux ctxt-info-v2.c; layout correctness provable only against hardware |
| Provenance + machine-readable manifest | [1] | research/ax211-api89/FIRMWARE-89.md + firmware-manifest.json |
| fw_gen staleness fix (regenerate on input change) | [1] | scripts/fw_gen.sh mtime logic; CI regenerates from fresh checkout |
| API 68 removal (no active fallback) | [1] | CI asserts the exclusive firmware set; history retains the old blobs (tag v2.4.0-ax211-reduced) |

## Command ABI (fw 89)

| Command | Status | Notes |
|---|---|---|
| SCAN_REQ_UMAC v17 (band in flags[31:30], psd_20) | [2] | Builder ported from Linux v7.3 scan.c; wire format needs hardware bring-up |
| PHY_CONTEXT_CMD v4 + RLC_CONFIG_CMD v2 | [2] | v3 path preserved for -68; v4 leaves rxchain reserved and sends RLC |
| SESSION_PROTECTION_CMD v2 (link id) | [2] | Same wire format, id semantics ported |
| TLC_MNG_CONFIG_CMD v4 | [2] | Existing v4 struct path now selected |
| POWER_TABLE_CMD v7 (4-byte struct) | [1] | Struct unchanged from v6; NO_SLEEP_TILL_D3 is D3-only (unused) |
| RX_BAID_ALLOCATION v2 (capa BAID_ML) | [2] | ADD/REMOVE ported; replaces ADD_STA immediate-BA on fw 89 |
| SCD_QUEUE_CONFIG v3 TVQM ADD/REMOVE | [2] | Dynamic queue alloc incl. fw-assigned mgmt queue; REMOVE fixes the TVQM leak (DRV-IWX-011) |
| ABI registry (reject out-of-range firmware) | [1] | iwx_fw_check_abi() table; logs the negotiated versions |
| Smart-Fifo offload (API 68) | [1] | SF_CFG_CMD skipped when advertised |
| Aux station fw-managed (capa MLD) | [2] | Manual ADD_STA skipped per Linux gating |

## Driver fixes from the audit (Phase C)

| Fix | Audit ID | Status |
|---|---|---|
| setPOWER OR-logic (both flags required) | DRV-AP-006 | [2] one-line fix, needs power-cycle test |
| Scan-result rate transcription | DRV-AP-016 | [1] CI compiles; logic self-evident |
| getSCAN_RESULT HalService identifier | DRV-AP-017 | [1] |
| RX BA reorder-buffer/mBuf leak on roam | DRV-11D-009 | [1] freed in ieee80211_ba_del on all paths |
| Watchdog on main workloop | DRV-11C-004 | [2] concurrency fix; stress-test on hardware |
| EAPOL key-length wraparound | REF-010 | [1] guarded subtraction |
| F_DESBSSID un-latch after association | DRV-11C-002 | [2] roaming behavior requires walk-test |
| joinBSSID follows internal roam | DRV-AP-005 | [2] |
| LinkStatus-up after silent re-auth | DRV-11C-007 | [2] |
| Idle scan park + restart hook | DRV-11C-003 | [2] idle power/RF behavior observable on hardware |
| In-place assoc retry + node poison | DRV-11C-005 | [2] |
| ADDBA initial ramp 1s -> 100ms | DRV-11D-008 | [2] throughput ramp observable |
| Real DELBA on teardown | DRV-11D-010 | [2] |
| PNVM failed-parse no longer dead-codes | DRV-IWX-008 (partial) | [1] flow corrected; the 2s wait retained (Linux-matching doorbell+wait semantics) |

## Known gaps (remaining work, category [3])

| Gap | Scope | Reference |
|---|---|---|
| WPA3-Personal SAE (H2E + hunting-and-pecking) | Port Eric-AirportItlwm's ieee80211_sae.c + BearSSL P-256, AKM classification in WCL join, PMF advertisement; IGTK/BIP key path in iwx_set_key; WCL setCIPHER_KEY IGTK case | audit DRV-11D-003/004, REF-004 |
| PMF/MFP (IGTK, BIP-GMAC) | Depends on SAE work; fw 89 supports the key shapes | DRV-11D-004 |
| 6 GHz band (channels, PSC scan, RNR) | Band-aware channel indexing in net80211 + WCL decode (channel > 196 currently dropped); scan v17 already supports the band encoding | DRV-11D-001, DRV-AP-003; Eric REF-005 (BE200-qualified only) |
| GCMP ciphers (WPA3-Enterprise) | No ieee80211_crypto_gcmp.c exists in any fork | DRV-11D-002 |
| SAR/PPAG transmit-power enforcement | No WRDS/EWRD/WGDS support (macOS lacks the Linux ACPI/UEFI sources; would need NVM/DSM tables) | LINUX-009; compliance gap |
| Scan completion by held results (ScanDone race) | Eric's keepWCLScanResult/finishWCLScan restructure; audit recommends verifying against airportd on 15.8 first | DRV-AP-011, REF-002/003 |
| Per-queue TX backpressure / mgmt exemption | qfullmsk global stall remains; design work + freeze risk (XPLAT-013) | DRV-11D-018 |
| 11r/11v/11k roam assistance | WCL roam surfaces are stubs | DRV-AP-012 |
| TVQM >256 TFDs (gen3 freeze) | Author TODO; cap retained deliberately | DRV-IWX-010, XPLAT-014 |
| Ad-hoc signing docs for stock Sequoia | kmutil refuses unsigned kexts with SIP | CI-005 |

## Build and verification

- Exclusive build: GitHub Actions "Build AX211 Sequoia Debug"
  (workflow_dispatch), `macos-15-intel`, Xcode 16.4, SDK MacOSX15.5,
  x86_64 Debug, CODE_SIGNING_ALLOWED=NO.
- Verification gate: Mach-O arch check, bundle id, OSBundleLibraries
  (incl. IOSkywalkFamily + corecapture), Info.plist lint, binary floor
  1.2MB, exclusive API-89 firmware set (source-level) + embedded-string
  checks, AX211 PCI IDs, sha256 manifests, undefined-symbol census.
- Latest artifact: `AirportItlwm-v2.4.0-AX211-Sequoia-Debug-<sha>.zip`
  (see `artifacts/` in the run; sha256 sidecar included).

A successful build is a build pass, not a validated Wi-Fi implementation;
every [2] item above requires the physical MSI test checklist.
