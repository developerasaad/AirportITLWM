#!/bin/bash
# collect-diagnostics.sh — AirportItlwm (Dell G3 3579) diagnostic collection
#
# Safe, read-only collection of the state needed to investigate driver issues.
# Produces a .tar.gz on the Desktop. Requires nothing but stock macOS.
# No passwords, key material, or network credentials are collected: the log
# predicates below target driver/interlock messages only.
#
# Usage: bash collect-diagnostics.sh [seconds_of_recent_logs]

set -u

LOG_SECONDS="${1:-300}"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUTDIR="/tmp/airportitlwm-diag-$STAMP"
OUTFILE="$HOME/Desktop/airportitlwm-diagnostics-$STAMP.tar.gz"

mkdir -p "$OUTDIR"
exec 2>"$OUTDIR/collector-errors.txt"

log() { echo "$*" | tee -a "$OUTDIR/summary.txt"; }

log "== AirportItlwm diagnostics $STAMP (collected by $(basename "$0")) =="

# --- host identity (no serials) ---
{
  echo "-- sw_vers"; sw_vers
  echo "-- Darwin version"; uname -r
  echo "-- model"; sysctl -n hw.model 2>/dev/null
  echo "-- CPU"; sysctl -n machdep.cpu.brand_string 2>/dev/null
  echo "-- boot-args"; sysctl -n boot-args 2>/dev/null
} >> "$OUTDIR/summary.txt" 2>&1

# --- kext identity & load state ---
{
  echo "-- kextstat / kmutil kext loaded?"
  kmutil showloading 2>/dev/null | grep -i -A1 -B1 "itlwm\|zxystd" || true
  echo "-- kext bundles on disk (searched standard locations)"
  for d in /Library/Extensions /System/Library/Extensions "$HOME/Library/Extensions" /Volumes/EFI/EFI/OC/Kexts /Volumes/EFI/EFI/CLOVER/kexts/Other; do
    [ -d "$d" ] && find "$d" -maxdepth 1 -iname "*itlwm*" -exec \
      sh -c 'echo "bundle: {}"; plutil -extract CFBundleVersion raw "{}/Contents/Info.plist" 2>/dev/null' \; 2>/dev/null
  done
  echo "-- loaded kext Info.plist"
  KEXT_PLIST=$(kextstat 2>/dev/null | grep -i "zxystd\|itlwm" | head -3)
  echo "$KEXT_PLIST"
} >> "$OUTDIR/kext-state.txt" 2>&1

# --- PCI Wi-Fi device identity ---
system_profiler SPUSBDataType SPThunderboltDataType 2>/dev/null | grep -i -B2 -A6 "intel\|8086\|wifi\|wireless" > "$OUTDIR/system-profiler-wifi.txt" 2>&1 || true
ioreg -r -l 2>/dev/null | grep -i -B3 -A12 "IOPCIEDeviceWrapper\|zxystd\|AirportItlwm" > "$OUTDIR/ioreg-airportitlwm.txt" 2>&1 || true

# --- network state ---
{
  echo "-- ifconfig (en0..en2, names only + status)"
  ifconfig 2>/dev/null | sed -n '1,80p'
  echo "-- networksetup -listallhardwareports"
  networksetup -listallhardwareports 2>/dev/null
} > "$OUTDIR/network-state.txt" 2>&1

# --- driver log excerpts (bounded window, driver-scoped predicates) ---
log "-- collecting last ${LOG_SECONDS}s of driver-relevant log"
log show --last "${LOG_SECONDS}s" --style compact 2>/dev/null \
  --predicate '(eventMessage CONTAINS[c] "itlwm") OR (eventMessage CONTAINS[c] "zxystd") OR (eventMessage CONTAINS[c] "iwm") OR (process == "airportd") OR (eventMessage CONTAINS "IO80211")' \
  > "$OUTDIR/driver.log" 2>>"$OUTDIR/collector-errors.txt" || true
log "-- kernel-only excerpt"
log show --last "${LOG_SECONDS}s" --style compact 2>/dev/null \
  --predicate '(sender == "kernel") AND ((eventMessage CONTAINS[c] "itlwm") OR (eventMessage CONTAINS[c] "iwm") OR (eventMessage CONTAINS[c] "iwx") OR (eventMessage CONTAINS "AirPort"))' \
  > "$OUTDIR/kernel-driver.log" 2>>"$OUTDIR/collector-errors.txt" || true

# --- panic / crash reports touching the driver (last 10, driver-scoped) ---
mkdir -p "$OUTDIR/panic-reports"
for f in $(ls -t "$HOME/Library/Logs/DiagnosticReports" 2>/dev/null | head -40); do
  case "$f" in
    *itlwm*|*Airport*|*panic*|*AirportItlwm*)
      cp "$HOME/Library/Logs/DiagnosticReports/$f" "$OUTDIR/panic-reports/" 2>/dev/null || true
      ;;
  esac
done
[ "$(ls -A "$OUTDIR/panic-reports" 2>/dev/null)" ] || rmdir "$OUTDIR/panic-reports" 2>/dev/null || true

# --- sleep/wake timeline (bounded) ---
log show --last "2d" --style compact 2>/dev/null \
  --predicate '(eventMessage CONTAINS "Entering Sleep") OR (eventMessage CONTAINS "Wake from") OR (process == "kernel" AND eventMessage CONTAINS "Sleep")' \
  > "$OUTDIR/sleep-wake.log" 2>>"$OUTDIR/collector-errors.txt" || true

# --- package ---
tar -czf "$OUTFILE" -C /tmp "airportitlwm-diag-$STAMP" \
  && log "Diagnostics written to: $OUTFILE"
rm -rf "$OUTDIR" 2>/dev/null
log "Done. Attach the .tar.gz to the corresponding GitHub issue."
