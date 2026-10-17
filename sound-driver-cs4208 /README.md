# CS4208 audio experiments on MacBook Pro 2015

This work started with [MrHogun/imac-a2115-linux](https://github.com/MrHogun/imac-a2115-linux),
which demonstrated extracting Apple's speaker tuning from macOS for an iMac.
The goal here was to use reverse engineering to develop driver support and
audio processing for **AppleHDA layout 128** on the **MacBookPro11,4 (2015)**
described in the [main README](../README.md): Intel Core i7-4770HQ, Cirrus Logic
CS4208, audio subsystem ID `0x106b8000`, and Linux `7.0.0-38-generic`.
The iMac's audio hardware and tuning were a starting point, not a compatible
profile for this MacBook.

The experiments addressed thin, metallic speaker sound and weak bass compared
with macOS on the same machine. This is a historical summary of the operations
and results recorded in [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md), through
October 11, 2026.

## Experiments and findings

| Experiment / operation | Result and conclusion |
| --- | --- |
| **Mixer and existing driver settings** — tested `model=mbp11`, HDA jack retasking, independent Speaker/Bass Speaker muting, and PipeWire soft mixer settings. | Independent mixer control was possible without PipeWire, but these changes did not establish the cause of the poor sound. |
| **Separate hardware playback streams** — compared a four-channel HDA stream with two stereo streams and built an experimental kernel patch. | The four-channel stream was silent; two independent stereo PCM devices worked. Listening confirmed both channels on each branch, using DACs `0x03` and `0x04` through `hw:PCH,0` and `hw:PCH,2`. |
| **PipeWire four-channel routing** — combined the two PCM devices into `cs4208.split4`. | Playback on all four logical channels was confirmed. FL/FR feed the primary branch and RL/RR the bass branch; these labels do not mean physical rear speakers. |
| **Initial layout 128 EQ port** — extracted AppleHDA data and implemented static filters, eventually using explicit `bq_raw` coefficients. | Both branches played, but quietly and with weak bass. The early port omitted five type-6 filters and Apple's dynamic processing; it did not establish macOS sound equivalence. |
| **Simpler crossovers and level checks** — tested high-pass cutoffs, branch isolation, multitone signals, and a bass-heavy music introduction. | Digital measurements matched the configured filters and exposed substantial attenuation. Early direct tests reproduced 150/200 Hz but not 80/100 Hz at the tested levels. These were not acoustic measurements and did not establish a physical speaker limit. |
| **Codec initialization and macOS reference analysis** — inspected registers, collected AppleHDA and IORegistry data from this Mac, and compared initialization code. | The collected data confirmed layout 128, variant 0, and both DAC-to-pin paths. A controlled initialization-bit A/B retest with the bass branch present produced no clear improvement, so the masks were not adopted as a fix. A polarity test also found no confirmed polarity fault. |
| **Startup and routing diagnosis** — investigated a missing bass output and repeated playback with explicit local targets. | PipeWire could start before the bass PCM was available, leaving DSP profiles visible without their bass branch. Earlier negative listening results from that state were unreliable. Startup guarding restored the branch; local playback made the introduction audible, though quiet. |
| **Virtual bass and balanced tuning** — tested Bankstown harmonics, reduced attenuation, and a simpler balanced crossover. | Initial virtual-bass attempts did not restore the desired sound. Direct A/B recording showed much greater attenuation through the early DSP profiles than through direct bass playback. Balanced tuning improved audibility somewhat. |
| **Enhanced bass profile** — added isolated Bankstown harmonics to the balanced bass branch. | The user preferred the harmonic-enhanced sample. An initial live mixer error was corrected using explicit signal inversion; the resulting live output matched the successful offline sample with about 0.0207% relative RMS error. This became `cs4208.harmonics`. |
| **Full macOS DSP experiment** — ran native Apple DSP routines in userspace, including EQ, Mozart, Loudness, DualBand, BuzzKill, and SplineLimiter. | The offline sample received a positive listening response and became a live profile. Routing supervision, login recovery, and CPU optimizations improved operation. Fixed software master gain, numerical substitutions, and Linux hardware control prevented any claim of bit-exact or acoustic equivalence to macOS. |
| **Hybrid macOS DSP + enhanced bass** — combined Apple's dynamics with the preferred enhanced-bass graph. | The hybrid was louder with audible bass, but sometimes rattled. Larger buffers eliminated new xruns in the recorded tests; added gain reserve reduced potential digital clipping. Acoustic resolution of the rattling was not confirmed. The user ultimately preferred the original enhanced-bass profile. |
| **Power, packaging, and headphone switching** — disabled the heavier experimental services, enabled bass suspension, packaged installation/removal, and added event-driven jack routing. | Two wake/idle cycles confirmed PCM closure and controller suspension; the user reported no pops or lost introductions. Installation retries and mixer argument handling were fixed. A stronger PCM readiness check and automatic direct headphone routing restored reliable switching; the user confirmed headphones and speakers worked correctly after unplugging. |

## Recorded outcome

The preferred result was **MB Speakers (enhanced bass)**, backed by the split
stereo PCM kernel patch, PipeWire routing, harmonic bass processing, startup
guarding, and automatic headphone switching. The full macOS DSP and hybrid
profiles were retained as experiments but disabled from automatic startup.

The October 10 installation package was subsequently updated with the October
11 fixes and English scripts/documentation. Its kernel module targets
`7.0.0-38-generic` specifically and is not managed by DKMS. The experiments
produced a working, user-preferred setup; they did not prove complete
reproduction of macOS speaker processing or acoustic performance.
