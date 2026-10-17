# Power consumption and responsiveness optimization for MacBookPro11,4

Prepared on October 11, 2026 for Ubuntu 26.04.1, an Intel i7-4770HQ, and integrated Intel graphics.

This guide builds on NilsHolgerson's [How to get maximum battery life on Linux](https://medium.com/@nilsholgerson.nh/how-to-get-maximum-battery-life-on-linux-feaac383bf04). The sections below cover its Ubuntu baseline, auto-cpufreq/laptop-mode-tools setup, and PowerTOP workflow, adapted to the findings on this MacBook. The original article's battery-life results concern different hardware and are not a target guaranteed by this guide.

## Tools

| Tool | Purpose in this guide |
| --- | --- |
| [PowerTOP](https://github.com/fenrus75/powertop) | Inspect power consumption, wakeups, and device tunables; optionally test automatic tuning. |
| [auto-cpufreq](https://github.com/AdnanHodzic/auto-cpufreq) | Manage CPU frequency policy and Turbo according to load and power source. |
| [laptop-mode-tools](https://github.com/rickysarraf/laptop-mode-tools) | Manage device power saving; CPU control is disabled in the configuration used here. |
| [power-profiles-daemon](https://gitlab.freedesktop.org/upower/power-profiles-daemon) | Desktop power profiles; check for conflicts before using auto-cpufreq. |
| [TLP](https://linrunner.de/tlp/) | Alternative power management suite; assess it as an alternative rather than adding it to this setup. |

## Baseline and initial setup

### Distribution and desktop

The source article uses Ubuntu and GNOME as its baseline. This guide documents Ubuntu on MacBookPro11,4. Compare measurements on the same machine, with the same brightness, applications, and workload, before deciding whether a desktop or distribution change helps.

### Install the tools on a fresh system

Skip installation if the tools are already installed. The optimization script below adjusts an existing installation; it is not a general installer.

```bash
sudo apt update
sudo apt install git powertop laptop-mode-tools
```

For a source installation of auto-cpufreq, review the [upstream installation instructions](https://github.com/AdnanHodzic/auto-cpufreq#installation) and installer before running:

```bash
git clone https://github.com/AdnanHodzic/auto-cpufreq.git
cd auto-cpufreq
sudo ./auto-cpufreq-installer
sudo auto-cpufreq --install
sudo auto-cpufreq --stats
```

The [auto-cpufreq documentation](https://github.com/AdnanHodzic/auto-cpufreq#configuring-auto-cpufreq) describes conflicts with power-profiles-daemon; its source installer disables that daemon when detected. Check the resulting service state rather than assuming all power managers can run together:

```bash
systemctl status auto-cpufreq.service laptop-mode.service power-profiles-daemon.service --no-pager
```

The script expects auto-cpufreq to be active, laptop-mode-tools configuration files to exist, and the `schedutil` governor to be available. It disables the laptop-mode-tools CPU modules while retaining device settings. Its checks are specific to the recorded setup; review unexpected configuration differences before proceeding.

## Findings before optimization

- `intel_cpufreq` driver, passive intel_pstate mode, and the `powersave` governor.
- All eight logical CPUs repeatedly measured at approximately 800 MHz.
- Turbo disabled; maximum allowed frequency limited to 2.2 GHz.
- auto-cpufreq and laptop-mode-tools active simultaneously; both can control the CPU.
- PowerTOP service failing because of typographic quotation marks and `— auto-tune` instead of `--auto-tune`.
- Sufficient free RAM, unused swap, temperature around 66 °C, zero thermal throttling counters, and no GPU errors found during the current boot.

## Changes applied by the script

1. Give auto-cpufreq exclusive control of the CPU. Disable the CPU frequency and intel_pstate modules in laptop-mode-tools while preserving its other settings.
2. On battery, use `schedutil` and `turbo = never`. Frequency can rise with load up to the base maximum of 2.2 GHz and fall to 800 MHz at idle.
3. On AC power, use `schedutil` and `turbo = auto`; auto-cpufreq controls Turbo availability under load.
4. Give the auto-cpufreq service an explicit configuration path so a user configuration cannot override it. Back up and remove existing manual governor/Turbo overrides.
5. Disable the failing PowerTOP service. Do not enable blanket `--auto-tune`, to avoid overlapping device management with laptop-mode-tools. Preserve the original service file and record its enablement/running state for rollback.

A low frequency at idle is normal. The goal is to let the CPU speed up during work, rather than keep it permanently at a high frequency. Power consumption under load may increase compared with the original 800 MHz state; battery life cannot be promised without comparing the same workload and brightness.

## Apply the optimization

From the repository root, run:

```bash
sudo python3 power-optimization/optimize.py
```

The original checkout used `sudo python3 /home/kamil/sound_driver/power-optimization/optimize.py`; use the path matching your checkout.

The script creates `/home/power-optimization`, saves backups and before/after snapshots, applies the settings, and verifies the service and governors on all CPUs. If an error occurs during application, it attempts to restore the original settings automatically. If a backup manifest already exists, it refuses to overwrite it; inspect the previous result first.

## Rollback

```bash
sudo python3 /home/power-optimization/optimize.py --rollback
```

This restores backed-up files, the original service enablement and running states, and the captured CPU settings. The originally failing PowerTOP service is enabled again but is not started automatically. Its original faulty configuration will therefore take effect on the next boot.

## Verification

`before.json` and `after.json` contain CPU configuration, service states, temperature, battery status, and a short computation benchmark with frequency samples taken under load. The verification result is also saved to `result.txt`. The short benchmark does not measure GNOME responsiveness or long-term battery life. The AC profile cannot be verified without connecting the charger.

After applying the changes, try switching windows, scrolling pages, and typing. Compare battery use for at least 15–30 minutes with the same brightness, applications, and similar work. After rebooting, check that the following file contains `schedutil`:

```bash
cat /sys/devices/system/cpu/cpufreq/policy0/scaling_governor
```

### Inspect consumption and tunables with PowerTOP

```bash
sudo powertop
```

On battery, observe the discharge rate over time. Use Tab to reach **Tunables**; pressing Enter on a selected entry changes its setting. Review individual entries before changing them. See the [PowerTOP documentation](https://github.com/fenrus75/powertop#running-powertop) for navigation and reporting options.

For the audited PowerTOP 2.15, **Bad** can mean a valid value differs from its exact preferred value. It does not always mean power saving is disabled. The [local PowerTOP audit](powertop-audit-2026-10-11.md) records four such entries: writeback timeout, audio codec power management, the internal keyboard/trackpad, and the card reader. It explains why audio and input-device settings were retained and why card-reader autosuspend needs a separate test.

## Optional: PowerTOP auto-tune

This section documents the source article's automatic tuning approach with corrected command syntax. **It is an alternative experiment, not a step required by the optimization script above.** The script deliberately disables `powertop.service` because laptop-mode-tools already manages device settings.

### One-time test

PowerTOP's [automated tuning option](https://github.com/fenrus75/powertop#automated-tuning) applies its recommended tunables in one pass:

```bash
sudo powertop --auto-tune
```

Before testing, record the current settings and review overlaps with laptop-mode-tools. In particular, the local audit records deliberate autosuspend exceptions for the keyboard/trackpad and card reader. After tuning, test input devices, audio, SD card access, and suspend/resume, then compare consumption under the same conditions.

### Apply at boot with systemd

Only enable this after a successful one-time test and after deciding which tool owns overlapping device settings. If `/etc/systemd/system/powertop.service` already exists, save a separate copy before replacing it; this manual change is outside the optimization script's file rollback.

First check the executable path:

```bash
command -v powertop
```

The unit below assumes `/usr/sbin/powertop`. Substitute the actual absolute path in `ExecStart` if different. Use plain ASCII quotation marks and the exact option `--auto-tune`:

```bash
sudo tee /etc/systemd/system/powertop.service > /dev/null <<'EOF_UNIT'
[Unit]
Description=PowerTOP automatic power tuning

[Service]
Type=oneshot
Environment="TERM=dumb"
ExecStart=/usr/sbin/powertop --auto-tune
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF_UNIT

sudo systemctl daemon-reload
sudo systemctl enable --now powertop.service
```

Check the result immediately and again after reboot:

```bash
systemctl status powertop.service --no-pager
journalctl -u powertop.service -b --no-pager
```

For this oneshot unit, `active (exited)` is expected after successful execution. The unit runs once at boot; it does not continuously enforce settings or automatically reapply them after resume. Other power managers may subsequently change the same tunables.

### Disable automatic tuning

```bash
sudo systemctl disable --now powertop.service
```

Stopping the service does not undo tunables already applied. Restore any service file saved before the experiment and run `sudo systemctl daemon-reload`. Reboot with auto-tune disabled so normal boot policies can reapply; compare with your recorded settings and explicitly restore any remaining differences. The script's `--rollback` restores its own recorded changes, not arbitrary changes made during this experiment.

## Sources

- Original inspiration: NilsHolgerson, [How to get maximum battery life on Linux](https://medium.com/@nilsholgerson.nh/how-to-get-maximum-battery-life-on-linux-feaac383bf04), February 19, 2026.
- [Linux CPU frequency scaling](https://www.kernel.org/doc/html/latest/admin-guide/pm/cpufreq.html).
- [Intel P-state driver](https://www.kernel.org/doc/html/latest/admin-guide/pm/intel_pstate.html).
- [Configuring auto-cpufreq](https://github.com/AdnanHodzic/auto-cpufreq#configuring-auto-cpufreq).
- [PowerTOP documentation and source](https://github.com/fenrus75/powertop).
- [Local PowerTOP 2.15 audit, October 11, 2026](powertop-audit-2026-10-11.md), including source references for the four audited tunables.

## Status

Creating or editing these files alone does not change the system. The script's changes are applied only after it runs successfully with administrator privileges and creates `result.txt`. The optional installation and PowerTOP commands above make their own changes when executed.
