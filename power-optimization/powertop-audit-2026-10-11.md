# Audit of four “Bad” entries in PowerTOP 2.15

Audited on October 11, 2026. No system settings were changed during this audit.

PowerTOP 2.15 compares basic sysfs tunables against an exact target string using `strcmp`. “Bad” can therefore also mean a different valid value, rather than only disabled power saving. This was verified directly in the v2.15 source code.

| Entry | Current state | Reason for “Bad” |
| --- | --- | --- |
| VM writeback timeout | dirty_writeback_centisecs=60000 (600 s), dirty_expire_centisecs=60000 | PowerTOP expects exactly 1500 (15 s). Laptop-mode-tools sets the interval from LM_BATT_MAX_LOST_WORK_SECONDS=600. A longer interval is not evidence of higher power consumption; it reduces periodic writes but allows unsynchronized data to remain unwritten for longer. This parameter alone does not determine actual data loss: other events and explicit application synchronization also trigger writes. |
| Audio codec power management | snd_hda_intel power_save=2, power_save_controller=Y | Power saving is enabled with a 2 s timeout. PowerTOP expects exactly 1. Laptop-mode-tools uses INTEL_HDA_DEVICE_TIMEOUT=2. There is no reason to change the value solely for the indicator color; the kernel documentation advises against an overly short 1 s timeout. Whether a particular codec actually enters a power-saving state also depends on open audio streams. |
| Apple Internal Keyboard / Trackpad | USB 1-12, 05ac:0274, power/control=on, wakeup=enabled, delay=2000 ms | Autosuspend is actually disabled. The device has usbhid and bcm5974 interfaces. Laptop-mode-tools excludes usbhid from autosuspend management as a compatibility exception for input devices. |
| Card Reader | USB 2-4, 05ac:8406, power/control=on, delay=2000 ms | Autosuspend is actually disabled. The usb-storage driver is among the laptop-mode-tools exceptions. Any attempt to enable autosuspend must be tested, including SD card insertion, reading, writing, and wakeup. |

Exception configuration: `/etc/laptop-mode/conf.d/runtime-pm.conf` contains `AUTOSUSPEND_RUNTIME_DEVTYPE_BLACKLIST="sd hub usbhid usb-storage"`. The `/usr/share/laptop-mode-tools/modules/runtime-pm` module also checks the interfaces under each device, so the usbhid exception applies to the entire internal keyboard/trackpad.

## Status of the previous optimization

`/home/power-optimization/result.txt` confirms that the schedutil governor was successfully applied to all CPUs and that a frequency of 2195 MHz was recorded during the test. These four entries are not evidence that CPU optimization failed.

## Recommendations

- Leave the audio and keyboard settings unchanged rather than adjusting them solely to obtain “Good”.
- For an NVMe SSD, consider a shorter writeback interval separately, such as 15–30 s, as a compromise for more frequent saving. Compare power consumption through measurement.
- The card reader is a candidate for a separate, reversible autosuspend test. Blanket PowerTOP auto-tune was not run during this audit.

## Sources

- https://github.com/fenrus75/powertop/blob/v2.15/src/tuning/tuning.cpp
- https://github.com/fenrus75/powertop/blob/v2.15/src/tuning/tuningsysfs.cpp
- https://github.com/fenrus75/powertop/blob/v2.15/src/tuning/tuningusb.cpp
- https://docs.kernel.org/sound/designs/powersave.html
- https://docs.kernel.org/admin-guide/sysctl/vm.html

## Record location

The audit record was saved at `/home/kamil/power-optimization/powertop-audit-2026-10-11.md`.
