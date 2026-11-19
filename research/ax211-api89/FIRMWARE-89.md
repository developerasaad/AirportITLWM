# Firmware API 89 Integration — Provenance and Port Record

## Firmware identity (pinned)

| Artifact | Value |
|---|---|
| ucode file | `iwlwifi-so-a0-gf-a0-89.ucode` |
| ucode size | 1,737,012 bytes |
| ucode sha256 | `698c913f938d9a8adce7ab9c049b1cd37daaa7473d8185f93e98f22733092f6b` |
| internal version | **89.d2579d43.0** (matches the confirmed running firmware on the target MSI Modern 14 C12MO / AX211 under Ubuntu 26.10) |
| build identifier | `release/core86:signed_remote:d2579d43` |
| PNVM file | `iwlwifi-so-a0-gf-a0.pnvm` |
| PNVM size | 55,176 bytes |
| PNVM sha256 | `776606c7b5d0f582b5ec78a591fb1e5e621a6efa670e8261f29114bbf1b0f8d1` |
| PNVM version TLV | `0x12c849a2` (4 SKU sections, 2 SEC_RT chunks each) |

## Provenance

Both artifacts were extracted from the Ubuntu 26.10 (stonking) Intel
wireless firmware package, which is the exact source the target machine
runs:

- Package: `linux-firmware-intel-wireless_20260915.git1522c78a-0ubuntu1_all.deb`
- Pool path: `pool/main/l/linux-firmware-intel-wireless/`
- Mirror: mirrors.edge.kernel.org/ubuntu
- Inner path: `usr/lib/firmware/intel/iwlwifi/`
- Package sha256: `87bef8c6dc3a0efd3765b71e8022795a7c152e088e61bfd9473a551468ee3a1f`

Licensing: Intel proprietary firmware under the terms of
`iwlwifi-firmware-license` (retained at repo root / firmware directory);
the driver remains GPLv2.

## Machine-readable manifest

`firmware-manifest.json` holds the parsed TLV data for the legacy API 68
blob (for comparison) and the API 89 blob: API bits, capability bits and
the full command/notification version table. Regenerate with:

    python3 tools/fw_parse.py itlwm/firmware/iwlwifi-so-a0-gf-a0-89.ucode --json firmware-manifest.json

## Command ABI: 68 → 89 delta (driver-visible)

Versioned commands changed by the firmware (from the CMD_VERSIONS TLV):

| Command | (group, cmd) | fw68 | fw89 | Action |
|---|---|---|---|---|
| SCAN_REQ_UMAC | (1, 0x0d) | 14 | **17** | builder accepts v14–v17 (shared layout); v17 encodes band in `channel_config[].flags[31:30]` |
| PHY_CONTEXT_CMD | (1, 0x08) | 3 | **4** | v4 struct identical; `rxchain_info` reserved — RX chains programmed via RLC_CONFIG_CMD |
| SESSION_PROTECTION_CMD | (3, 0x05) | 1 | **2** | same layout; `id_and_color` carries the fw link id (== mac id, non-MLD) |
| TLC_MNG_CONFIG_CMD | (5, 0x0f) | 3 | **4** | v4 struct (already present in driver) |
| POWER_TABLE_CMD | (1, 0x77) | 6 | **7** | 4-byte struct unchanged; v7 adds NO_SLEEP_TILL_D3 (D3 only) |
| REDUCE_TX_POWER_CMD | (1, 0x9f) | 6 | **8** | not sent by this driver (no SAR/PPAG support yet — open compliance gap) |
| SCD_QUEUE_CONFIG_CMD | (5, 0x17) | — | **3 (new)** | TVQM queue ADD/REMOVE/MODIFY; mgmt queue becomes fw-assigned; queue REMOVE on BA teardown |
| RX_BAID_ALLOCATION_CONFIG_CMD | (5, 0x16) | — | **2 (new)** | RX BlockAck BAID management, mandatory (capa BAID_ML_SUPPORT) |
| RLC_CONFIG_CMD | (5, 0x08) | 2 | 2 | now actually sent (phy ctxt v4 path) |

Commands whose CMD_VERSIONS entries were **removed** in fw 89 (size/API-bit
negotiation, matching `iwl_fw_lookup_cmd_ver()` defaults):
ADD_STA (was v12), ADD_STA_KEY (v3), REMOVE_STA (v2), MAC_CONTEXT_CMD (v5),
BINDING_CONTEXT_CMD (v2), TIME_QUOTA_CMD (v2), SCD_QUEUE_CFG legacy (v2),
STATISTICS_CMD (v1), STA_HE_CTXT_CMD (v2).

New API bits: 66 (NO_HOST_DISABLE_TX), 67 (INT_DBG_BUF_CLEAR),
68 (SMART_FIFO_OFFLOAD — driver now skips SF_CFG_CMD).
New capa bits: 32 (FRAGMENTED_PNVM_IMG — segmented PNVM DRAM layout),
63 (BAID_ML_SUPPORT), 110 (MLD_API_SUPPORT — fw-managed aux station),
plus LARI/scan/BT-coex bits not used by this driver.
Removed capa bits: 0 (D0I3), 47 (FTM_CALIBRATED), 93 (DBG_BUF_ALLOC).

## Driver port (commit series)

1. **Firmware set**: only `iwlwifi-so-a0-gf-a0-89.ucode` + `.pnvm` embedded;
   14 legacy blobs removed; `fw_gen.sh` regenerates `FwBinary.cpp` when
   inputs change (staleness fix); Xcode project references updated.
2. **Scan v15–v17**: version dispatch extended (v14–v17 share the 1940-byte
   `iwx_scan_req_umac_v14` layout); v17 band encoding in
   `channel_config[].flags[31:30]`; v5 channel-config union member with
   `psd_20` added for 6 GHz.
3. **PHY context v4 + RLC**: v3/v4 dispatch; v4 leaves `rxchain_info` zero
   and sends `RLC_CONFIG_CMD` (32-byte v2 struct) after ADD/MODIFY.
4. **Session protection v2**: id field carries the link id for v2+.
5. **HE station context**: absent version entry now defaults to v2 (v1
   without API MBSSID_HE) instead of failing with EOPNOTSUPP.
6. **Aux station**: skipped when capa MLD_API_SUPPORT is advertised.
7. **RX aggregation**: BAID allocation via RX_BAID_ALLOCATION_CONFIG_CMD
   when capa BAID_ML_SUPPORT is set (ADD/REMOVE, v2 remove by sta+tid).
8. **TVQM v3**: queue allocation through SCD_QUEUE_CONFIG_CMD ADD;
   management queue dynamically allocated (fw-assigned qid);
   queue REMOVE + driver-ring free on BA teardown (closes the TVQM
   queue leak — audit DRV-IWX-011).
9. **PNVM**: chunk-preserving parse; segmented (scatter-descriptor) DRAM
   layout when capa FRAGMENTED_PNVM_IMG is set, contiguous otherwise;
   failed parse no longer dead-codes into the doorbell path.
10. **Smart FIFO**: skipped when API SMART_FIFO_OFFLOAD is advertised.
11. **ABI registry**: `iwx_fw_check_abi()` validates the implemented
    command-version ranges after firmware load and rejects out-of-range
    firmware with an explicit log.
12. **Device matching**: IOPCIMatch reduced to the AX211 SO+GF family
    (0x51F0, 0x54F0, 0x7F70); AX210 (2725/ty), AX411 (51F1/gf4) and
    MA-family (7E40) IDs removed together with their firmware.

## Firmware policy

API 89 is the exclusive target; the API 68 integration is preserved in Git
history (tag `v2.4.0-ax211-reduced`, branch `ax211-baseline-validated`) as
the recoverable baseline, not as an active fallback.
