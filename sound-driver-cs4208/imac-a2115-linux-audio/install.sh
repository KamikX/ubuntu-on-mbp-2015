#!/usr/bin/env bash
# iMac 27" A2115 (iMac19,1) -- speaker setup for Linux.
#
# Two parts, because the kernel driver only takes effect after a reboot:
#   1. the out-of-tree cs8409 driver, without which this machine has no sound
#   2. the PipeWire filter chain carrying Apple's own speaker tuning
#
# Run as your normal user; it asks for sudo where it needs it. Running it twice
# is safe -- the second run skips whatever is already in place.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CARD=alsa_card.pci-0000_00_1f.3
SINK=alsa_output.pci-0000_00_1f.3.analog-surround-40
PROFILE=output:analog-surround-40+input:analog-stereo
DRIVER_SRC="${XDG_CACHE_HOME:-$HOME/.cache}/snd_hda_macbookpro"

info() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m!!\033[0m  %s\n' "$*"; }
die()  { printf '\033[1;31mERROR\033[0m %s\n' "$*" >&2; exit 1; }

[[ $EUID -eq 0 ]] && die "run as your normal user, not root"

# --- hardware check --------------------------------------------------------
# The tuning in this repo belongs to one machine. On anything else the filter
# curves describe speakers that are not there, so refuse rather than mislead.
model=$(cat /sys/class/dmi/id/product_name 2>/dev/null || echo unknown)
if [[ $model != iMac19,1 ]]; then
  warn "this machine reports '$model', not iMac19,1 (iMac 27\" A2115, 2019)."
  warn "The driver step may still help; the speaker tuning will not fit."
  read -rp "Continue anyway? [y/N] " reply
  [[ ${reply,,} == y ]] || exit 1
fi

command -v pactl >/dev/null || die "pactl not found -- install pipewire-pulse"
command -v systemctl >/dev/null || die "systemd required"

# --- package manager -------------------------------------------------------
if command -v pacman >/dev/null; then
  PM=pacman
  install_pkgs() { sudo pacman -S --needed --noconfirm "$@"; }
  HEADERS=(linux-headers)   # matches the `linux` kernel; use linux-lts-headers on LTS
  DEPS=(git dkms base-devel wget)
elif command -v apt-get >/dev/null; then
  PM=apt
  install_pkgs() { sudo apt-get install -y "$@"; }
  HEADERS=("linux-headers-$(uname -r)")
  DEPS=(git dkms build-essential wget patch)
elif command -v dnf >/dev/null; then
  PM=dnf
  install_pkgs() { sudo dnf install -y "$@"; }
  HEADERS=("kernel-devel-$(uname -r)")
  DEPS=(git dkms make gcc wget patch)
else
  die "unsupported package manager -- install git, dkms, kernel headers and a compiler by hand"
fi

# --- step 1: kernel driver -------------------------------------------------
driver_installed() { dkms status 2>/dev/null | grep -q snd_hda_macbookpro; }
apple_path_active() { journalctl -k -b 2>/dev/null | grep -qi "Primary patch_cs8409 NOT FOUND trying APPLE"; }

install_driver() {
  info "Step 1/3: kernel driver (snd_hda_macbookpro)"

  if driver_installed; then
    info "DKMS module already installed -- skipping build"
    return 1
  fi

  info "Installing build dependencies via $PM"
  [[ $PM == apt ]] && sudo apt-get update -qq
  install_pkgs "${DEPS[@]}" "${HEADERS[@]}"

  if [[ -d $DRIVER_SRC/.git ]]; then
    info "Updating driver source in $DRIVER_SRC"
    git -C "$DRIVER_SRC" pull --ff-only
  else
    info "Cloning davidjo/snd_hda_macbookpro into $DRIVER_SRC"
    mkdir -p "$(dirname "$DRIVER_SRC")"
    git clone --depth=1 https://github.com/davidjo/snd_hda_macbookpro "$DRIVER_SRC"
  fi

  info "Building and installing via DKMS (this takes a minute)"
  ( cd "$DRIVER_SRC" && sudo ./install.cirrus.driver.sh -i )
  return 0
}

# --- step 2: audio configuration -------------------------------------------
install_config() {
  info "Step 2/3: PipeWire filter chain, WirePlumber rule, user service"

  install -Dm644 "$REPO/config/pipewire/90-imac-speakers.conf" \
                 "$HOME/.config/pipewire/pipewire.conf.d/90-imac-speakers.conf"
  install -Dm644 "$REPO/config/wireplumber/51-imac-surround.conf" \
                 "$HOME/.config/wireplumber/wireplumber.conf.d/51-imac-surround.conf"
  install -Dm644 "$REPO/config/systemd/imac-audio.service" \
                 "$HOME/.config/systemd/user/imac-audio.service"

  # Without this the amplifiers go silent whenever the HDA controller
  # runtime-suspends -- after a system suspend, most visibly. See the README.
  if ! cmp -s "$REPO/config/modprobe/99-imac-audio.conf" /etc/modprobe.d/99-imac-audio.conf; then
    info "Disabling HDA runtime power management (needs sudo)"
    sudo install -Dm644 "$REPO/config/modprobe/99-imac-audio.conf" \
                        /etc/modprobe.d/99-imac-audio.conf
    warn "That takes effect at the next boot."
  fi

  systemctl --user daemon-reload
  systemctl --user enable imac-audio.service >/dev/null
  info "Installed and enabled imac-audio.service"
}

apply_now() {
  info "Step 3/3: applying without a reboot"

  pactl set-card-profile "$CARD" "$PROFILE" ||
    die "could not select the four-channel profile -- is the driver loaded? (see README, Troubleshooting)"

  systemctl --user restart pipewire pipewire-pulse wireplumber
  sleep 3

  pactl set-sink-volume "$SINK" 100%
  if pactl set-default-sink imac_speakers 2>/dev/null; then
    info "Default output is now 'iMac Speakers'"
  else
    warn "the filter sink did not appear; check: journalctl --user -u pipewire -b | grep -i filter"
  fi
}

# --- run -------------------------------------------------------------------
if install_driver; then
  echo
  info "Driver installed. The kernel only binds it at boot, so a reboot is needed now."
  info "After rebooting, run this script again to finish the audio setup."
  read -rp "Reboot now? [y/N] " reply
  [[ ${reply,,} == y ]] && systemctl reboot
  exit 0
fi

if ! apple_path_active && ! grep -q "CS8409/CS42L83" /proc/asound/card*/codec#0 2>/dev/null; then
  warn "the Apple driver does not look active yet. If you just installed it, reboot first."
fi

install_config
apply_now

echo
info "Done. Verify with:  ./verify.sh"
