#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
set -euo pipefail
[[ $EUID != 0 ]] || { echo 'Run without sudo.' >&2; exit 1; }
for unit in pipewire-pulse.socket pipewire.socket wireplumber.service pipewire-pulse.service pipewire.service; do
    systemctl --user stop "$unit" || true
done
for unit in pipewire.socket pipewire-pulse.socket pipewire.service pipewire-pulse.service wireplumber.service; do
    systemctl --user start "$unit"
done
