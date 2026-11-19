#!/usr/bin/env python3
"""Intel ucode TLV parser for the AX211 API-89 port.

Parses an Intel iwlwifi *.ucode container (TLV format) and emits a
machine-readable manifest: firmware version, API bits, capability bits,
command/notification version table, and image sections.

Usage:
    fw_parse.py <file.ucode> [<file2.ucode> ...] [--json OUT]

Used to pin and verify iwlwifi-so-a0-gf-a0-89.ucode (build d2579d43) and to
diff its advertised ABI against the legacy API-68 blob.
"""

import json
import struct
import sys
import hashlib

# TLV type IDs (iwl firmware file format, see if_iwxreg.h / Linux fw/file.h)
TLV_NAMES = {
    0: "INVALID", 1: "INST", 2: "DATA", 3: "INIT", 4: "INIT_DATA",
    5: "BOOT", 8: "MEM_DESC", 9: "SEC_RT", 10: "SEC_INIT", 11: "SEC_WOWLAN",
    12: "SEC_UCODE", 13: "PKG_NAME", 15: "SW_VERSION", 16: "HDR",
    17: "HDR_RAW", 18: "GSC", 19: "SEC_RT_USNIFFER", 20: "PAGING",
    22: "N_SCAN_CHANNELS", 23: "GEO_INFO", 24: "FW_VERSION_LEGACY",
    25: "PHY_SKU", 29: "API_CHANGES_SET", 30: "ENABLED_CAPABILITIES",
    31: "CSCAN", 32: "FW_DBG_CONF", 34: "FW_DBG_DEST", 36: "FW_VERSION",
    48: "CMD_VERSIONS", 49: "FWDBG", 250: "DEFAULT_CALIB",
}

# Canonical IDs from Linux drivers/net/wireless/intel/iwlwifi/fw/file.h:
CANON = {
    "FW_VERSION": 36,
    "API_CHANGES_SET": 29,
    "ENABLED_CAPABILITIES": 30,
    "CMD_VERSIONS": 48,
    "N_SCAN_CHANNELS": 22,
    "PHY_SKU": 25,
}

# Command group names (Linux v7.3 fw/api/commands.h: enum iwl_mvm_command_groups)
GRP = {
    0: "LEGACY", 1: "LONG", 2: "SYSTEM", 3: "MAC_CONF", 4: "PHY_OPS",
    5: "DATA_PATH", 6: "SCAN", 8: "LOCATION", 9: "BT_COEX",
    11: "PROT_OFFLOAD", 12: "REGULATORY_NVM", 15: "DEBUG",
    16: "STATISTICS",
}


def parse(path):
    data = open(path, "rb").read()
    out = {
        "file": path.split("/")[-1],
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }
    magic = struct.unpack_from("<I", data, 4)[0]
    out["magic"] = "%08x" % magic
    out["human_readable"] = data[8:72].split(b"\x00")[0].decode(errors="replace")
    # struct iwx_tlv_ucode_header: zero(4) magic(4) human_readable[64]
    #                               ver(4) build(4) ignore(8)  -> TLVs at 88
    # struct iwx_ucode_tlv: uint32 type; uint32 length; data[]  (no padding)
    out["ver_word"] = "%08x" % struct.unpack_from("<I", data, 72)[0]
    out["build_word"] = "%08x" % struct.unpack_from("<I", data, 76)[0]
    pos = 88
    tlvs = []
    api_bits = set()
    capa_bits = set()
    cmd_versions = []
    sections = []
    fw_version = None
    n_scan_channels = None
    phy_sku = None
    while pos + 8 <= len(data):
        t, l = struct.unpack_from("<II", data, pos)
        payload = data[pos + 8 : pos + 8 + l]
        if len(payload) < l:
            break
        entry = {"type": t, "name": TLV_NAMES.get(t, "TLV_%d" % t), "len": l}
        if t == CANON["FW_VERSION"] and l == 12:
            a, b, c = struct.unpack("<III", payload)
            fw_version = {
                "major": a, "minor": b, "local": c,
                "string": "%d.%x.%d" % (a, b, c),
            }
            entry["value"] = fw_version["string"]
        elif t == CANON["API_CHANGES_SET"] and l == 8:
            idx, flags = struct.unpack("<II", payload)
            bits = [i + 32 * idx for i in range(32) if flags & (1 << i)]
            api_bits.update(bits)
            entry["api_index"] = idx
            entry["bits"] = bits
        elif t == CANON["ENABLED_CAPABILITIES"] and l == 8:
            idx, cap = struct.unpack("<II", payload)
            bits = [i + 32 * idx for i in range(32) if cap & (1 << i)]
            capa_bits.update(bits)
            entry["capa_index"] = idx
            entry["bits"] = bits
        elif t == CANON["CMD_VERSIONS"] and l % 4 == 0:
            for off in range(0, l, 4):
                cmd, grp, cv, nv = struct.unpack_from("<BBBB", payload, off)
                cmd_versions.append({
                    "group": grp,
                    "group_name": GRP.get(grp, "?%d" % grp),
                    "cmd": cmd, "cmd_ver": cv, "notif_ver": nv,
                })
            entry["count"] = len(cmd_versions)
        elif t in (1, 2, 3, 4, 5, 9, 10, 11, 18, 19) or t >= 250:
            if l >= 8:
                idx, flags = struct.unpack_from("<II", payload, 0)
                entry["sec"] = {
                    "idx": idx, "flags": "%08x" % flags, "bytes": l - 8,
                }
                sections.append(entry["sec"])
        elif t == CANON["N_SCAN_CHANNELS"] and l == 4:
            n_scan_channels = struct.unpack("<I", payload)[0]
            entry["value"] = n_scan_channels
        elif t == CANON["PHY_SKU"] and l == 4:
            phy_sku = struct.unpack("<I", payload)[0]
            entry["value"] = "%08x" % phy_sku
        tlvs.append(entry)
        pos += 8 + l
    out["fw_version"] = fw_version
    out["n_scan_channels"] = n_scan_channels
    out["phy_sku"] = "%08x" % phy_sku if phy_sku is not None else None
    out["api_bits"] = sorted(api_bits)
    out["capa_bits"] = sorted(capa_bits)
    out["cmd_versions"] = sorted(
        cmd_versions, key=lambda c: (c["group"], c["cmd"])
    )
    out["sections"] = sections
    out["tlv_count"] = len(tlvs)
    return out


def main():
    args = sys.argv[1:]
    json_out = None
    if "--json" in args:
        i = args.index("--json")
        json_out = args[i + 1]
        args = args[:i] + args[i + 2:]
    manifests = [parse(p) for p in args]
    for m in manifests:
        print("== %s ==" % m["file"])
        print("  size=%d sha256=%s" % (m["size"], m["sha256"]))
        print("  human_readable: %s" % m["human_readable"])
        print("  fw_version: %s" % (m["fw_version"] or {}).get("string"))
        print("  n_scan_channels=%s phy_sku=%s"
              % (m["n_scan_channels"], m["phy_sku"]))
        print("  api_bits (%d): %s" % (len(m["api_bits"]), m["api_bits"]))
        print("  capa_bits (%d): %s" % (len(m["capa_bits"]), m["capa_bits"]))
        print("  cmd_versions (%d):" % len(m["cmd_versions"]))
        for c in m["cmd_versions"]:
            print("    grp=%2d %-16s cmd=%3d cmd_ver=%d notif_ver=%d"
                  % (c["group"], c["group_name"], c["cmd"],
                     c["cmd_ver"], c["notif_ver"]))
        print("  sections: %s" % [(s["idx"], s["bytes"]) for s in m["sections"]])
        print()
    if len(manifests) == 2:
        a, b = manifests
        print("== DIFF %s -> %s ==" % (a["file"], b["file"]))
        print("api only in A:", sorted(set(a["api_bits"]) - set(b["api_bits"])))
        print("api only in B:", sorted(set(b["api_bits"]) - set(a["api_bits"])))
        print("capa only in A:", sorted(set(a["capa_bits"]) - set(b["capa_bits"])))
        print("capa only in B:", sorted(set(b["capa_bits"]) - set(a["capa_bits"])))
        ka = {(c["group"], c["cmd"]): c["cmd_ver"] for c in a["cmd_versions"]}
        kb = {(c["group"], c["cmd"]): c["cmd_ver"] for c in b["cmd_versions"]}
        for k in sorted(set(ka) | set(kb)):
            va, vb = ka.get(k), kb.get(k)
            if va != vb:
                print("cmd grp=%d cmd=%d : A=%s B=%s" % (k[0], k[1], va, vb))
    if json_out:
        with open(json_out, "w") as f:
            json.dump(manifests, f, indent=1)
        print("manifest written: %s" % json_out)


if __name__ == "__main__":
    main()
