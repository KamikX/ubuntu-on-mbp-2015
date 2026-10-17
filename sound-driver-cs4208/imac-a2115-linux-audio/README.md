# iMac 27" A2115 — speakers on Linux

[![Stand With Ukraine](https://raw.githubusercontent.com/vshymanskyy/StandWithUkraine/main/badges/StandWithUkraine.svg)](#support-ukraine)

Sound on the **iMac 27" A2115 (2019, `iMac19,1`)** under Linux — working at all,
and then sounding the way it does under macOS.

Two problems, two fixes:

1. **No sound.** The mainline kernel driver never initialises this machine's
   amplifiers. An out-of-tree driver does.
2. **Bad sound.** The iMac has four speakers — two tweeters, two woofers — and
   Linux sends the same full-range signal to all four. No crossover: tweeters
   get bass they cannot make, woofers get treble they smear.

The second fix uses **Apple's own tuning**, read out of macOS. Not a fit by ear,
not a guess: the crossover frequencies, the filter curves and the gain structure
below are the numbers macOS itself runs on this hardware.

---

## Install

```bash
git clone https://github.com/MrHogun/imac-a2115-linux-audio
cd imac-a2115-linux-audio
./install.sh          # installs the driver, then asks you to reboot
./install.sh          # run again after the reboot to finish
./verify.sh           # confirms the crossover really is doing something
```

Using Claude Code? Point it at [`CLAUDE.md`](CLAUDE.md) — it is the full
procedure, including the mistakes that waste an afternoon.

---

## Where this was tested

Everything below was done on one machine, and every claim in this README was
measured on it:

| | |
|---|---|
| Hardware | iMac19,1 — iMac 27" 5K, 2019 (A2115), board `Mac-AA95B1DDAB278B95` |
| CPU | Intel Core i5-9600K |
| Firmware | Apple 2094.80.5.0.0 |
| Audio | Cirrus Logic CS8409 + CS42L83, subsystem `0x106b1000`, 4× TAS5764 amps |
| Distro | Omarchy 4.0.3 (Arch Linux) |
| Kernel | 7.2.3-arch1-3 |
| PipeWire | 1.6.8 (WirePlumber 0.5.x) |
| Driver | `davidjo/snd_hda_macbookpro`, commit `89b22ff` (2026-09-06), via DKMS |
| Tuning source | macOS 15.7.9, `AppleHDA.kext` layout 16 |

The install script also knows `apt` and `dnf`, and the audio configuration is
plain PipeWire — but only the setup above has actually been run end to end.
Reports from other distributions are welcome.

---

## Why there is no sound by default

The mainline `snd_hda_codec_cs8409` module supports **Dell laptops only**. You
can check without trusting anyone:

```bash
zstdcat "$(modinfo -F filename snd_hda_codec_cs8409)" | strings | grep -c -i apple
# 0
zstdcat "$(modinfo -F filename snd_hda_codec_cs8409)" | strings | grep -o 'CS8409_[A-Z]*' | sort -u
# CS8409_BULLSEYE, CS8409_CYBORG, CS8409_DOLPHIN, CS8409_ODIN, CS8409_WARLOCK  -- Dell codenames
```

On an Apple machine the codec falls through to a generic path. Pins get
configured, an analog sink appears, PipeWire is happy — and the four TAS5764
amplifiers are never programmed, so nothing comes out.

[davidjo/snd_hda_macbookpro](https://github.com/davidjo/snd_hda_macbookpro)
carries the Apple initialisation sequences, reverse-engineered from macOS. It is
the only reason this machine makes sound.

---

## The speakers

Four drivers, one amplifier each, on the codec's I2C bus — straight out of
Apple's own data:

| Amplifier | I2C | Driver | ALSA channel |
|---|---|---|---|
| TAS5764 | `0x6c` | left tweeter | FL |
| TAS5764 | `0x6d` | right tweeter | FR |
| TAS5764 | `0x6e` | left woofer | RL |
| TAS5764 | `0x6f` | right woofer | RR |

They are exposed by the ALSA profile `analog-surround-40`. The mapping was
confirmed by measurement: at 200 Hz the rear pair is 6–11 dB louder.

---

## What macOS actually does

macOS keeps the DSP for the internal speakers inside the HDA driver, at
`AppleHDA.kext/Contents/Resources/layout<N>.xml.zlib` — a zlib-compressed plist
fragment per machine. Which one applies is chosen by Apple's firmware and is
only visible from macOS: `ioreg -l | grep layout-id`. On this iMac it is **16**.

Decoded, layout 16 describes this chain:

```
stereo in
  → DspEqualization32           input EQ, 12 sections per channel
  → DspMozartCompressor
  → DspLoudness
  → DspMozartCompressorDualBand
  → DspGainStage                −5.0 dB
  → Dsp2To4Splitter             fan out to four
       ├─ tweeters  gain −2.5 dB → 10 sections, 2 cascaded highpasses @ 3.0 kHz
       └─ woofers   gain  0.0 dB → 15/16 sections, 3 cascaded lowpasses @ 1.39 kHz
  → DspSplineLimiter / BuzzKill / ControlFreak4ch
  → Dsp4ChOutput
```

Filter sections are stored as `type / frequency / Q / gain`, with the floats
written as their int32 bit patterns. Type 0 is a lowpass, 1 a highpass, 4 a
peaking section — identifiable from where Apple places them.

So Apple's crossover is **asymmetric**: woofers rolled off at 1.39 kHz with a
6th-order slope, tweeters at 3.0 kHz with a 4th-order slope. Nobody would land
on that by ear, and it is the single biggest reason a hand-tuned crossover
sounds wrong on this machine.

### What this repo reproduces

Everything static: the input EQ, the gain structure, the crossover, and all 75
filter sections across the three equalisers — 83 PipeWire nodes in total.

### What it does not

Apple's level-dependent stages: `DspMozartCompressor`, `DspLoudness`,
`DspMozartCompressorDualBand`, `DspBuzzKill`, `DspControlFreak4ch`, the spline
limiters, and an 8-sample delay on the tweeter branch. These are dynamics, not a
fixed response, and PipeWire's builtin filters have no equivalent. In practice:
the tonal balance matches, but macOS will hold loud material together slightly
better than this does.

---

## Signal chain as installed

```
applications (stereo)
  └→ "iMac Speakers"  [imac_speakers]   ← default output, a normal stereo sink
       input EQ ×2 · pre-gain · split ─┬→ tweeter EQ → FL, FR
                                       └→ woofer  EQ → RL, RR
  └→ alsa_output.pci-0000_00_1f.3.analog-surround-40
```

Applications see an ordinary stereo output and need no configuration.

---

## Verifying

`./verify.sh` plays a tone through the filter sink and reads what arrives at each
of the four hardware channels, from the sink's monitor. It is a digital
measurement — no microphone, no opinion. On the test machine:

```
tone             FL        FR        RL        RR
            tweeter   tweeter    woofer    woofer
150 Hz       -91.0    -91.0    -37.2    -36.8  dB
800 Hz       -91.0    -91.0    -43.4    -42.7  dB
9000 Hz      -35.9    -35.2    -91.0    -91.0  dB
```

−91 dB is digital silence: at 150 Hz nothing at all reaches the tweeters, at
9 kHz nothing reaches the woofers.

---

## Re-extracting the tuning yourself

Nothing here has to be taken on trust. With your own macOS install and
`apfs-fuse`:

```bash
sudo tools/mount-macos.sh                 # mounts the System volume read-only
tools/extract-apple-tuning.py --macos /mnt/macos/root --layout 16 \
    -o data/layout16-dsp.json
tools/generate-filter-chain.py            # regenerates the PipeWire config
```

`apfs-fuse` cannot write APFS, so the macOS install is never at risk. Note that
on Catalina and later the volume holding your files is the *Data* volume; the
kexts live on the System volume, which the script locates for you.

To adapt this to another Mac, read its `layout-id` under macOS and pass it to
`--layout`. Whether the result is right depends on that machine having the same
kind of speaker set — check the chain the extractor prints.

---

## Files

```
├── install.sh                 driver + configuration, idempotent
├── uninstall.sh               removes it again
├── verify.sh                  digital crossover measurement
├── CLAUDE.md                  step-by-step procedure for Claude Code
├── config/
│   ├── pipewire/90-imac-speakers.conf       the filter chain (generated)
│   ├── wireplumber/51-imac-surround.conf    hold the four-channel profile
│   ├── modprobe/99-imac-audio.conf          disable HDA runtime power management
│   └── systemd/imac-audio.service           re-apply after login
├── data/layout16-dsp.json     Apple's decoded DSP chain
└── tools/
    ├── mount-macos.sh         mount the macOS System volume read-only
    ├── extract-apple-tuning.py   layout*.xml.zlib → JSON
    └── generate-filter-chain.py  JSON → PipeWire config
```

---

## Troubleshooting

**No sound after installing the driver.** It binds at boot — reboot. Then
`cat /proc/asound/card*/codec#0 | grep Codec` must say `CS8409/CS42L83`. Seeing
`Primary patch_cs8409 NOT FOUND trying APPLE` in `journalctl -k` is correct: it
means the Apple path was taken.

**`imac_speakers` never appears.** The filter chain targets the four-channel
sink, so the profile has to be active first:
`pactl set-card-profile alsa_card.pci-0000_00_1f.3 output:analog-surround-40+input:analog-stereo`,
then `systemctl --user restart pipewire pipewire-pulse wireplumber`. If it still
does not appear: `journalctl --user -u pipewire -b | grep -i filter`.

**Only two speakers play.** The card fell back to stereo — that profile has a much
higher priority, which is what `51-imac-surround.conf` and the user service are for.
Check with `pactl list cards | grep "Active Profile"`.

**Quiet.** Apple's chain runs −5 dB of headroom before the crossover and cuts far
more than it boosts. Keep the hardware sink at full:
`pactl set-sink-volume alsa_output.pci-0000_00_1f.3.analog-surround-40 100%`
(the service does this at login).

**`verify.sh` shows similar numbers on all four channels.** Audio is bypassing the
filter chain — confirm `pactl info | grep "Default Sink"` says `imac_speakers`.
If something previously grabbed the card with `aplay -D plughw:...`, PipeWire
logs `Device or resource busy` and every measurement stays wrong until it is
restarted.

**Silence after suspend, or after the machine sat idle.** The CS8409's I2C
bridge — how the amplifiers are programmed — is powered from the HDA controller.
When runtime power management suspends the controller, the codec's resume
handler is never called and amplifier programming quietly does nothing: the
digital path runs, the pin is enabled, no error is logged anywhere, and the
speakers stay silent. `install.sh` writes `/etc/modprobe.d/99-imac-audio.conf`
to turn that off; it applies at the next boot. Confirm with
`cat /sys/module/snd_hda_intel/parameters/power_save` → `0`.
Same fault, same machine: [davidjo#209](https://github.com/davidjo/snd_hda_macbookpro/issues/209).

Once the codec is in that state, **reboot** — it cannot be revived in place.
`echo 1 > /sys/class/sound/hwC0D0/reconfig` fails with `error -22`, and
reloading the module oopses the kernel. Both were tried here so you do not have to.

**It broke after a kernel update.** DKMS rebuilds the module automatically, but if
the kernel headers were missing at update time it silently does not:
`dkms status` should list `snd_hda_macbookpro` for the running kernel.

---

## Credits

- [davidjo/snd_hda_macbookpro](https://github.com/davidjo/snd_hda_macbookpro) —
  the driver, and the reverse engineering behind it. Without it this machine is
  silent; everything here builds on that work.
- Apple — the tuning data, read from macOS on the machine that shipped with it.
  No Apple file is redistributed here; `data/layout16-dsp.json` holds decoded
  filter parameters, and the tools let you reproduce it from your own install.

## Disclaimer

Built by someone without a background in DSP or kernel development, with help
from Claude Code (Opus 5), by extracting Apple's own data rather than inventing
values. Tested on exactly one machine, in one room, by one pair of ears. There is
no claim of bit-exact parity with macOS — the dynamics stages are absent, and
they matter at high volume. If you know this domain and something here is wrong,
a pull request is very welcome.

## Support Ukraine

This was written in Ukraine. If it saved you an evening, consider
[supporting Ukraine](https://u24.gov.ua/).

## License

MIT — see [LICENSE](LICENSE). The licence covers the code in this repository.
