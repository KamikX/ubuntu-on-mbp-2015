#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
kernel_release=${KERNEL_RELEASE:-$(uname -r)}
if [[ "$kernel_release" != 7.0.0-38-generic ]]; then
    echo 'This package is prepared only for 7.0.0-38-generic.' >&2
    exit 1
fi
kernel_headers=${KERNEL_HEADERS:-/lib/modules/$kernel_release/build}
compiler=${CC:-x86_64-linux-gnu-gcc-15}
command -v "$compiler" >/dev/null || {
    echo 'GCC 15 is missing: sudo apt install gcc-15' >&2; exit 1;
}
[[ -f "$kernel_headers/Module.symvers" ]] || {
    echo 'Complete kernel headers including Module.symvers are missing.' >&2; exit 1;
}
make -C "$kernel_headers" M="$root/hda/codecs/cirrus" \
    CC="$compiler" -j"$(nproc)" modules 2>&1 | tee "$root/build.log"
module="$root/hda/codecs/cirrus/snd-hda-codec-cs420x.ko"
vermagic=$(modinfo -F vermagic "$module")
[[ "${vermagic%% *}" == "$kernel_release" ]] || {
    echo "Incorrect vermagic: $vermagic" >&2; exit 1;
}
modinfo -F parm "$module"
echo "Built: $module"
echo 'The module is not installed yet.'
