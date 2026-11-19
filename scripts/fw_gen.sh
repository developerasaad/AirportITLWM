#!/bin/sh

#  fw_gen.sh
#  itlwm
#
#  Created by qcwap on 2020/3/10.
#  Copyright © 2020 钟先耀. All rights reserved.
#
#  Generates include/FwBinary.cpp (zlib-compressed firmware blobs) from
#  every file in itlwm/firmware/.
#
#  The output is regenerated when any firmware file or the generator is
#  newer than the existing FwBinary.cpp. This guarantees a stale generated
#  file can never silently keep newly selected firmware out of the binary.
target_file="${PROJECT_DIR}/include/FwBinary.cpp"
script_file="${PROJECT_DIR}/scripts/zlib_compress_fw.py"

while [ $# -gt 0 ];
do
    case $1 in
    -P) fw_files=$2
    shift
    ;;

    esac
    shift
done

needs_build=0
if [ ! -f "$target_file" ]; then
    needs_build=1
else
    for src in "$fw_files"/*; do
        [ -f "$src" ] || continue
        if [ "$src" -nt "$target_file" ]; then
            needs_build=1
            break
        fi
    done
    if [ -f "$script_file" ] && [ "$script_file" -nt "$target_file" ]; then
        needs_build=1
    fi
fi

if [ "$needs_build" = "0" ]; then
    exit 0
fi

python3 "${script_file}" "${target_file}" "${fw_files}"
