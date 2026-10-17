#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
set -euo pipefail
kernel_release=${1:-7.0.0-38-generic}
[[ $EUID == 0 ]] || { echo 'Run sudo ./rollback.sh' >&2; exit 1; }
[[ "$kernel_release" == 7.0.0-38-generic ]] || exit 1
configuration=/etc/modprobe.d/cs4208-split-test.conf
destination="/lib/modules/$kernel_release/updates/cs4208-split-test"
if [[ -e "$configuration" ]] && ! grep -q '^# cs4208-split-test experimental module$' "$configuration"; then
    echo 'The configuration file was modified; automatic removal stopped.' >&2
    exit 1
fi
rm -f -- "$configuration" "$destination/snd-hda-codec-cs420x.ko"
if [[ -d "$destination" ]]; then
    rmdir -- "$destination"
fi
depmod -a "$kernel_release"
update-initramfs -u -k "$kernel_release"
echo 'Experiment removed. The original module will load after a reboot.'
