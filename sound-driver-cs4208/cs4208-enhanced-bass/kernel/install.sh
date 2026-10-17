#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
kernel_release=$(uname -r)
[[ $EUID == 0 ]] || { echo 'Run sudo ./install.sh' >&2; exit 1; }
[[ "$kernel_release" == 7.0.0-38-generic ]] || {
    echo 'Incorrect kernel; installation stopped.' >&2; exit 1;
}
[[ $(cat /sys/class/dmi/id/product_name) == MacBookPro11,4 ]] || {
    echo 'Incorrect model; installation stopped.' >&2; exit 1;
}
module="$root/hda/codecs/cirrus/snd-hda-codec-cs420x.ko"
[[ -f "$module" ]] || { echo 'Run ./build.sh first' >&2; exit 1; }
vermagic=$(modinfo -F vermagic "$module")
[[ "${vermagic%% *}" == "$kernel_release" ]] || exit 1
modinfo -F parm "$module" | grep -q '^split_speakers:' || exit 1
if command -v mokutil >/dev/null && \
   LC_ALL=C mokutil --sb-state 2>/dev/null | grep -q 'SecureBoot enabled'; then
    echo 'Secure Boot is enabled. Automatic installation of the unsigned module has been stopped.' >&2
    echo 'First sign the module using your own enrolled MOK.' >&2
    exit 1
fi
destination="/lib/modules/$kernel_release/updates/cs4208-split-test"
configuration=/etc/modprobe.d/cs4208-split-test.conf
[[ ! -e "$destination" && ! -e "$configuration" ]] || {
    echo 'The experiment already exists; use rollback.sh first.' >&2; exit 1;
}
install -d -m 0755 "$destination"
install -m 0644 "$module" "$destination/snd-hda-codec-cs420x.ko"
install -m 0644 "$root/modprobe/cs4208-split-test.conf" "$configuration"
depmod -a "$kernel_release"
update-initramfs -u -k "$kernel_release"
echo 'Installed. The original module remains in kernel/sound/hda/codecs/cirrus/.'
echo 'The active module will change after a reboot. Run sudo reboot.'
