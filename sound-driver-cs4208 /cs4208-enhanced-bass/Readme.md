# Enhanced bass + suspend: backup, manual installation and removal

Working setup recorded on **October 10, 2026**, MacBookPro11,4, CS4208.
The user confirmed that enhanced bass sounds best, with no pops or lost track
introductions when waking from idle. The bass output suspends after 5 seconds
of inactivity; measurements also confirmed that the audio controller suspended.
Both macOS DSP experiments are disabled and are excluded from this installation.

**This folder is self-contained:** it includes the driver, source, patch,
Bankstown, profile, support files, licenses, and a backup of the recorded volume
levels. It does not require the original sound_driver folder or mac_data.
The operating system packages listed below are not included in the archive.
Neither AppleHDA nor the test music is required.

The driver and included source target **kernel 7.0.0-38-generic only**,
Ubuntu kernel package 7.0.0-38.38, amd64. There is no DKMS integration: this
modified module will not rebuild automatically after a kernel update. A different
kernel requires separate adaptation and verification. Tested system: Ubuntu
26.04.1, PipeWire 1.6.2, WirePlumber 0.5.13; exact versions are recorded in
current-machine/versions.txt.

## Contents and backup

- kernel/: the exact installed .ko, all required source, patch, and build/install/rollback scripts.
- kernel/modprobe/: separate configuration for split_speakers + mbp11/index/MSI.
- pipewire/: only split4 and enhanced bass, including the 5-second timeout.
- wireplumber/: primary PCM and software mixer rules.
- vendor/bankstown.lv2/: the installed binary and both TTL files.
- support/: startup guard and audio service restart helpers.
- current-machine/: ALSA hardware state, PipeWire volumes, original root
  configurations, and user configurations from the snapshot, **for backup only**.
- reference/: measurements, source/build records, and older profiles; these are not installed.
- licenses/: licenses. SHA256SUMS: content verification.

Copy the entire folder, or the supplied .tar.gz and its .sha256 file, to another
drive. Make this backup before uninstalling. Verify the folder before building
or making changes; compilation may intentionally change the .ko and create
additional files.

```bash
cd /home/kamil/sound_driver/saved-setup/cs4208-enhanced-bass-2026-10-10
sha256sum -c SHA256SUMS
```

If copying only the archive, run these commands in the folder containing the
archive and its .sha256 file:

```bash
sha256sum -c cs4208-enhanced-bass-2026-10-10.tar.gz.sha256
tar -xzf cs4208-enhanced-bass-2026-10-10.tar.gz
cd cs4208-enhanced-bass-2026-10-10
```

Extract it into a separate folder that does not already contain an older,
modified copy. For the manual reinstall test, follow this order:
A1 → A2 → reboot → A3 → B1/B2 → reboot → B3 → optional B4 → B5.

After moving the package, open a terminal in its new folder. All relative paths
below start there. Do not copy the entire contents of current-machine/user-config
back during a clean installation: that backup also contains old experiments.

## A. Manually remove the existing setup on this Mac

This procedure also covers the existing installation without the new package's
manifest. Pause music, close Settings/Sound, and unplug wired headphones.
The commands remove only the named project files; the project folder and its
backups remain. Audio will return through the distribution's driver after reboot.

### A1. User profiles and startup guard — WITHOUT sudo

```bash
systemctl --user disable --now cs4208-jack-route.service
systemctl --user disable --now cs4208-macos-chain.service cs4208-macos-enhanced.service

rm -f ~/.config/pipewire/pipewire.conf.d/80-cs4208-split4.conf
rm -f ~/.config/pipewire/pipewire.conf.d/90-cs4208-layout128-eq.conf
rm -f ~/.config/pipewire/pipewire.conf.d/91-cs4208-simple.conf
rm -f ~/.config/pipewire/pipewire.conf.d/92-cs4208-virtualbass.conf
rm -f ~/.config/pipewire/pipewire.conf.d/93-cs4208-balanced.conf
rm -f ~/.config/pipewire/pipewire.conf.d/94-cs4208-harmonics.conf
rm -f ~/.config/wireplumber/wireplumber.conf.d/51-cs4208-soft-mixer.conf
rm -f ~/.config/wireplumber/wireplumber.conf.d/80-cs4208-primary-test.conf
rm -f ~/.config/systemd/user/pipewire.service.d/20-cs4208-wait.conf
rm -f ~/.config/systemd/user/cs4208-macos-chain.service
rm -f ~/.config/systemd/user/cs4208-macos-enhanced.service
rm -f ~/.config/cs4208-snapshot/wait-for-cs4208.py
rm -f ~/.config/cs4208-snapshot/jack-route.py
rm -f ~/.config/systemd/user/cs4208-jack-route.service

rm -f ~/.lv2/bankstown.lv2/bankstown.so
rm -f ~/.lv2/bankstown.lv2/bankstown.ttl
rm -f ~/.lv2/bankstown.lv2/manifest.ttl

systemctl --user daemon-reload
```

If the DSP units are no longer available, a disable command may report
Unit not found; those experiments are already disabled in the recorded setup.
Files named .conf.before-* are not loaded as configuration and need not be
deleted. Do not remove all of ~/.config or other plugins. Remove the startup
guard before uninstalling the bass PCM.

### A2. Modified module and modprobe configuration — with sudo

The recorded /etc/modprobe.d/alsa-base.conf also contains two older project
settings. The following command removes only those exact two lines. A backup
of the complete file is in current-machine/alsa-base.conf; other system settings
are preserved.

```bash
sudo sed -i \
  -e '/^options snd-hda-intel model=mbp11 index=0$/d' \
  -e '/^options snd-hda-intel enable_msi=1$/d' \
  /etc/modprobe.d/alsa-base.conf

sudo rm -f /etc/modprobe.d/cs4208-split-test.conf
sudo rm -f /lib/modules/7.0.0-38-generic/updates/cs4208-split-test/snd-hda-codec-cs420x.ko
sudo rmdir /lib/modules/7.0.0-38-generic/updates/cs4208-split-test
sudo depmod -a 7.0.0-38-generic
sudo update-initramfs -u -k 7.0.0-38-generic
sudo reboot
```

Removing the .ko does not change the module already loaded into memory:
the actual rollback takes effect after reboot. There is no need to enable the
old hda-jack-retask.conf.disabled file or the unused firmware.

### A3. Verify the original driver after reboot

```bash
uname -r
modinfo -n snd_hda_codec_cs420x
aplay -l
```

The module path should be under the distribution's kernel/sound/... directory
(and may end in .ko.zst), rather than updates/cs4208-split-test. The separate
CS4208 Bass Stereo output should be absent. Select the standard analog output
in sound settings. The original speaker output will sound different from enhanced
bass. Successful manual removal does not necessarily create an installation
manifest.

## B. Manually install the driver and enhanced bass

Pause music. Run all commands from the extracted package folder.

### B1. System and dependencies

```bash
uname -r
cat /sys/class/dmi/id/product_name
sha256sum -c SHA256SUMS
sudo apt install kmod python3 alsa-utils mokutil pipewire pipewire-bin \
  pipewire-pulse wireplumber libpipewire-0.3-modules libspa-0.2-modules
mokutil --sb-state
```

MacBookPro11,4, amd64, and 7.0.0-38-generic are required. If Secure Boot is enabled,
do not proceed with an unsigned module; this package does not include custom MOK
setup. The supplied .ko is an exact copy of the working installed module, so
**compilation is not required** on this exact kernel. To build from source instead:

```bash
sudo apt install gcc-15 make linux-headers-7.0.0-38-generic
bash kernel/build.sh
```

Do not force this source or binary onto another kernel. Remove or disable only
conflicting custom model=/index=/patch= settings; hda-jack-retask is not restored.

### B2. Manually install the module and configuration

First inspect the module: the output should show vermagic 7.0.0-38-generic and
split_speakers.

```bash
modinfo -F vermagic kernel/hda/codecs/cirrus/snd-hda-codec-cs420x.ko
modinfo -F parm kernel/hda/codecs/cirrus/snd-hda-codec-cs420x.ko

sudo install -d -m 755 /lib/modules/7.0.0-38-generic/updates/cs4208-split-test
sudo install -m 644 kernel/hda/codecs/cirrus/snd-hda-codec-cs420x.ko \
  /lib/modules/7.0.0-38-generic/updates/cs4208-split-test/snd-hda-codec-cs420x.ko
sudo install -m 644 kernel/modprobe/cs4208-split-test.conf /etc/modprobe.d/cs4208-split-test.conf
sudo depmod -a 7.0.0-38-generic
sudo update-initramfs -u -k 7.0.0-38-generic
sudo reboot
```

These commands assume that the experiment has been uninstalled: do not overwrite
another custom module or unrelated configuration at the same paths. The
distribution's .ko remains unchanged.

After reboot, reopen a terminal in the package folder:

```bash
cat /sys/module/snd_hda_codec_cs420x/parameters/split_speakers
modinfo -n snd_hda_codec_cs420x
aplay -l
```

Expected results: Y, a path under updates/cs4208-split-test, and **CS4208 Bass Stereo**
on card PCH, device 2. If it is missing, resolve module loading before installing
the profile.

### B3. Manually install user files — WITHOUT sudo

If another setup already exists, back up files with the same names before copying.
After the removal procedure above, these named files should be absent.

```bash
mkdir -p ~/.config/pipewire/pipewire.conf.d
mkdir -p ~/.config/wireplumber/wireplumber.conf.d
mkdir -p ~/.lv2/bankstown.lv2
mkdir -p ~/.config/cs4208-snapshot
mkdir -p ~/.config/systemd/user/pipewire.service.d

install -m 644 pipewire/80-cs4208-split4.conf ~/.config/pipewire/pipewire.conf.d/
install -m 644 pipewire/94-cs4208-harmonics.conf ~/.config/pipewire/pipewire.conf.d/
install -m 644 wireplumber/51-cs4208-soft-mixer.conf ~/.config/wireplumber/wireplumber.conf.d/
install -m 644 wireplumber/80-cs4208-primary-test.conf ~/.config/wireplumber/wireplumber.conf.d/
install -m 644 vendor/bankstown.lv2/bankstown.so ~/.lv2/bankstown.lv2/
install -m 644 vendor/bankstown.lv2/bankstown.ttl ~/.lv2/bankstown.lv2/
install -m 644 vendor/bankstown.lv2/manifest.ttl ~/.lv2/bankstown.lv2/
install -m 644 support/wait-for-cs4208.py ~/.config/cs4208-snapshot/
install -m 644 support/jack-route.py ~/.config/cs4208-snapshot/
install -m 644 support/cs4208-jack-route.service ~/.config/systemd/user/

printf '%s\n' '[Service]' \
  'ExecStartPre=/usr/bin/python3 %h/.config/cs4208-snapshot/wait-for-cs4208.py' \
  > ~/.config/systemd/user/pipewire.service.d/20-cs4208-wait.conf
```

Do not install the user profile with sudo. The installed startup guard does not
reference the original project or archive location. Set the hardware Master to
0 dB and restart the services:

```bash
amixer -c PCH -- sset Master 0dB unmute
amixer -c PCH sset Speaker 100% unmute
amixer -c PCH sset 'Bass Speaker' 100% unmute
systemctl --user daemon-reload
bash support/restart-audio.sh
python3 manage-user.py select --initial
systemctl --user enable --now cs4208-jack-route.service
python3 manage-user.py check
```

--initial sets the profile volume to 75%, the primary and split outputs to unity
gain, and the bass output to a linear gain of 1.405254, matching the preferred
settings. Installation sets the hardware Master to 0 dB. Selecting without
--initial preserves volume: `python3 manage-user.py select`.

### 3.5 mm headphone jack

On October 11, 2026, the user confirmed working headphone audio and correct
restoration of the speakers after unplugging the jack.

The `cs4208-jack-route.service` service responds to sound card events. On insertion,
it selects the direct analog output without speaker DSP, unmutes the headphone
mixer, and mutes the speakers. On removal, it restores
`MB Speakers (enhanced bass)`, the primary and bass speakers, and unity gain on
the primary branch. The initial headphone software volume is 35%; subsequent
headphone volume changes are remembered for the lifetime of the service.
The startup check waits for a successful ALSA PCM open, rather than merely
checking for entries in /proc, to prevent the bass output from disappearing
because of a boot race.

```bash
systemctl --user status cs4208-jack-route.service
journalctl --user -u cs4208-jack-route.service -n 30
```

### B4. Optionally restore the exact saved volume levels

On this same Mac, after successful installation, with music paused:

```bash
python3 restore-current-levels.py --dry-run
python3 restore-current-levels.py
```

This restores the complete ALSA mixer and the volume/mute state of the four
relevant sinks. It replaces the installation defaults with the state saved on
October 10, including the hardware Master (the archived value may differ from
0 dB). It restores levels only, not experimental profiles. Enhanced bass becomes
the default output.

To save the hardware mixer state for subsequent boots, after checking the volume:

```bash
sudo alsactl store PCH
```

This changes the system ALSA state. The virtual profile's volume may not survive
a restart because its original configuration uses state.restore-props=false;
run restore-current-levels.py again if an exact restoration is needed.

### B5. Check suspension and audio recovery

Play music, pause it, close Settings/Sound, and wait at least 10 seconds:

```bash
cat /proc/asound/card0/pcm2p/sub0/status
cat /sys/bus/pci/devices/0000:00:1b.0/power/runtime_status
```

PCM2 should report closed. In the verified test, the controller reported suspended;
another active stream or microphone can prevent the card from suspending.
When playback resumes, both branches should play without losing the beginning.
The user confirmed no pops or lost introductions on this device.

## C. Removal after manual reinstallation

Follow A1 and A2, then reboot and perform the A3 checks. The two sed expressions
in A2 have no effect after a clean reinstall, because model/index/MSI are then
in the separate file being removed. Files in reference and current-machine
are never installed automatically.

## D. Alternative: supplied scripts

The supplied scripts' text and messages are in English. Installation defaults
to a hardware Master of 0 dB and a profile volume of 75%.

October 11, 2026 fix: negative volume arguments are passed using `amixer --`
to prevent installation from stopping. If an earlier attempt failed with
`invalid option`, rerun `bash install-user.sh` from this corrected package.
The script verifies that installed files match, preserves the original backup,
and completes activation. It rejects modified files or a different package.
It waits up to 120 seconds for outputs to appear because RTKit delays were
observed on this system.

To automate this installation instead of copying files manually:

```bash
sudo bash kernel/install.sh
sudo reboot
# After reboot, reopen the package folder:
bash install-user.sh --dry-run
bash install-user.sh
```

These scripts check the model/kernel, back up the named user files, and create
a manifest in ~/.local/share/cs4208-enhanced-bass-snapshot/. Repeating the same
installation preserves the backup and runs activation again; different or modified
files cause it to stop. The original distribution kernel module is not overwritten.
User installation sets Master to 0 dB and the profile to 75%, as in B3.
B4 remains an optional way to restore the saved volume levels.

Manifest-based removal is available only after installation through install-user.sh:

```bash
bash remove-user.sh
sudo bash kernel/rollback.sh
sudo reboot
```

remove-user.sh restores previous files from backup. If automatic installation was
performed over an old experiment, removal could restore it; the clean procedure A
is therefore recommended before a new test. Manual copying creates no manifest:
use manual removal A/C. If files have been modified, remove-user.sh refuses to
delete them to preserve your changes.

## Packaging verification

The active profiles, plugin, and .ko were compared with the packaged files.
The source was built for the same kernel in a separate temporary folder, without
installation. The user installer and its restoration behavior were tested in
an isolated staging folder. File checksums and archive contents were verified.
The live setup was not uninstalled or reinstalled during the original packaging.

On October 11, 2026, the negative amixer argument failure was reproduced, and
installation retry with backup preservation was tested in an isolated folder.
The interrupted installation on this machine was successfully completed: all
outputs appeared and cs4208.harmonics became the default profile at 75% volume.
The complete manual uninstall/reinstall cycle on the machine remains a user-run
procedure described by this guide.
