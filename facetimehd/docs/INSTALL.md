# FaceTime HD camera installation

This guide describes how to install the built-in FaceTime HD camera driver using
the installer included in this repository. See the
[FaceTime HD README](../facetimehd/README.md) for the project overview,
compatibility information, and installer details.

The system recorded in the [repository README](../README.md) is a
MacBookPro11,4 running Ubuntu 26.04.1 LTS with kernel `7.0.0-38-generic`.
These are reference system details, not confirmation of a successful camera
installation.

## 1. Prepare the system

You need an internet connection, administrator access through `sudo`, and kernel
headers matching the running kernel. The installer installs build tools, DKMS,
Git, curl, V4L2 utilities, and kernel headers through APT.

Check the running kernel and update the package index:

```bash
uname -r
sudo apt update
sudo apt install "linux-headers-$(uname -r)"
```

If headers are unavailable for the running kernel, resolve that before continuing.
If you install and boot a different kernel, check its header package again.

## 2. Check the installer before running it

From the root of this repository:

```bash
cd facetimehd
less scripts/install.sh
```

**The current installer needs a firmware correction before use.** In
[`scripts/install.sh`](../facetimehd/scripts/install.sh), `FIRMWARE_URL` is set to
`https://debian.org`. This is a website, not the camera firmware. The script only
checks whether the downloaded file exists, so that check cannot establish that
the firmware is valid.

Before proceeding, obtain the required Apple camera firmware using the
[upstream firmware project](https://github.com/patjak/facetimehd-firmware), then
adapt the installer's firmware step to install the resulting `firmware.bin` into
`/lib/firmware/facetimehd/firmware.bin`. Do not run the script unchanged or assume
that its commented download URL provides a valid firmware binary.

The installer also hardcodes DKMS version `0.7.0.1`. Check that this matches the
`PACKAGE_VERSION` in the downloaded driver's `dkms.conf`; otherwise, adapt the
DKMS commands to the source version being installed.

## 3. Run the corrected installer

Once the firmware and DKMS checks above are resolved, run the following from the
`facetimehd` directory:

```bash
sudo bash scripts/install.sh
```

The installer downloads the driver source into `/usr/src/facetimehd-driver`,
registers and builds it with DKMS, installs the firmware, and attempts to load
the `facetimehd` module. DKMS supports rebuilding the module after kernel
updates, provided the matching headers are installed and the build succeeds.

If installation completes without errors, reboot:

```bash
sudo reboot
```

## 4. Verify the camera

After rebooting:

```bash
dkms status
lsmod | grep facetimehd
v4l2-ctl --list-devices
sudo journalctl -k -b | grep -Ei 'facetimehd|bcwc|firmware'
```

Confirm that DKMS reports the driver as installed for the running kernel, that
`facetimehd` is loaded, and that V4L2 lists the camera. The device number may vary;
it is not necessarily `/dev/video0`.

For a visual test, install and open Cheese:

```bash
sudo apt install cheese
cheese
```

Select the FaceTime HD camera if multiple devices are available. In a browser,
also allow camera access for the site you are using.

## Troubleshooting and maintenance

If the module is not loaded, try `sudo modprobe facetimehd` and inspect the
kernel log above. After a kernel update, check the matching headers and run
`sudo dkms autoinstall` if a rebuild is needed.

See the [troubleshooting guide](../facetimehd/docs/TROUBLESHOOTING.md) for more
diagnostics. Its example DKMS version is `0.1`; use the version reported by your
own `dkms status` output when following version-specific commands.

Optional power tuning is documented separately in the
[power management guide](../facetimehd/docs/POWER.md) and is not required to
install the camera driver.

For removal, see the [README uninstallation section](../facetimehd/README.md#uninstallation)
and review [`scripts/uninstall.sh`](../facetimehd/scripts/uninstall.sh) first.
The current uninstaller targets DKMS version `0.1`, whereas the installer targets
`0.7.0.1`; correct that mismatch for your installed version before using it.
