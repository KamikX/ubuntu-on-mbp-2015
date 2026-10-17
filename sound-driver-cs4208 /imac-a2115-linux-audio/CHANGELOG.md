# Changelog

## 3.0 — Apple's own tuning

Complete rewrite. Earlier versions reconstructed a tuning; this one reads the
one macOS actually uses.

**Source of the data.** `AppleHDA.kext` layout 16 — the DSP chain Apple's own
driver runs on this machine, selected by its firmware (`ioreg -l | grep layout-id`).
Crossover frequencies, filter sections and gain structure are taken verbatim.

**What changed against 1.x / 2.x**

- Crossover: was a 4th-order Linkwitz-Riley at 800 Hz, chosen by hand. Apple's is
  asymmetric — woofers lowpassed at 1.39 kHz (3 cascaded sections), tweeters
  highpassed at 3.0 kHz (2 cascaded). This alone accounted for most of the
  difference in how it sounds.
- EQ: was the inverse of the AID20 `PressureResponse` FIR for the woofers plus
  Cirrus BootCamp `CONF_0911` values for the tweeters. Naively inverting a
  measured pressure response produced a ~+14 dB lift around 500 Hz. Replaced by
  Apple's 75 filter sections across three equalisers.
- Removed the 4096-tap FIR convolvers and the AID20 pipeline. They depended on a
  JSON file extracted to an external disk, which nobody else could reproduce.
- Added `tools/` so the tuning can be re-extracted from any owner's macOS
  install, and `data/layout16-dsp.json` so it can be inspected without one.
- Added `verify.sh`: a digital measurement of the crossover through the sink
  monitor, instead of trusting the ear.
- Added `CLAUDE.md` for Claude Code, including the measurement mistakes that
  make a working setup look broken.
- `install.sh` now covers pacman, apt and dnf, checks the machine really is an
  `iMac19,1`, and is safe to re-run.
- Default sink renamed `imac_dsp_in` → `imac_speakers`.

## 2.0

AID20 `PressureResponse` inverse FIR convolution, 4096-tap minimum phase.

## 1.x

Kernel driver via DKMS, four-channel profile, biquad approximations of AID20 and
Cirrus BootCamp data, 800 Hz crossover.
