# FaceTime HD Camera for Linux

**Enable the built-in Apple FaceTime HD camera on 2013–2015 Intel MacBooks running Ubuntu/Linux**

---

## Overview

This project provides an automated installer that makes the Apple FaceTime HD camera work reliably on older Intel MacBooks running Linux. It eliminates the need for manual driver compilation, firmware extraction, and patching by wrapping everything into a single, reproducible installation script.

### What This Does

- Automatically builds and installs the `facetimehd` (bcwc_pcie) driver using DKMS
- Downloads and extracts the required Apple firmware
- Configures automatic driver rebuilds after kernel updates
- Optionally tunes power management for better battery life and quieter fans

---

## Compatibility

### Tested MacBook Models

- MacBookPro11,1
- MacBookPro11,2
- MacBookPro11,3
- MacBookPro11,4
- Other 2013–2015 Intel MacBooks with FaceTime HD (BCM1570)

### Supported Operating Systems

- Ubuntu 22.04 LTS and newer
- Ubuntu 24.04 LTS
- Ubuntu 26.04 LTS
- Other Debian-based distributions (may require adaptation)

### Kernel Support

- Linux kernel 6.x series
- Linux `7.0.0-38-generic`
- Automatic rebuild support via DKMS

---

## Installation

### Prerequisites

Ensure your system is up to date:

```bash
sudo apt update && sudo apt upgrade -y
```

### Install

Clone the repository and run the installer:

```bash
cd facetimehd
chmod +x scripts/*.sh
sudo ./scripts/install.sh
```

Reboot your system to load the driver:

```bash
sudo reboot
```

### Verify Installation

After rebooting, test the camera:

```bash
# Check if the driver loaded
lsmod | grep facetimehd

# List video devices
v4l2-ctl --list-devices

# Test with Cheese
cheese
```

You should see the "Apple FaceTime HD" camera listed as `/dev/video0`.

---

## Usage

The camera should now work automatically with:

- **Cheese** (GNOME Camera)
- **Google Meet**
- **Zoom**
- **Microsoft Teams**
- Any application using V4L2 (Video4Linux2)

---

## Optional: Power Management

Reduce heat and fan noise while improving battery life:

```bash
sudo ./scripts/power-tune.sh
```

This script installs and configures TLP with optimized settings for MacBooks.

---

## Troubleshooting

If the camera doesn't work after installation, see the [troubleshooting guide](docs/TROUBLESHOOTING.md).

### Common Issues

**Camera not detected:**

```bash
# Reload the driver
sudo modprobe -r facetimehd
sudo modprobe facetimehd
```

**No /dev/video0:**

```bash
# Check DKMS status
dkms status

# Check kernel logs
dmesg | grep facetimehd
```

**Permission denied:**

```bash
# Add your user to the video group
sudo usermod -aG video $USER
# Log out and back in
```

For detailed troubleshooting, see [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

---

## Uninstallation

Run the bundled uninstaller from the `facetimehd` directory:

```bash
sudo ./scripts/uninstall.sh
```

The current script attempts to unload the module and remove the driver and
firmware. However, it hardcodes DKMS version `0.1`, while the installer uses
`0.7.0.1`. It also continues if unloading fails. Follow the steps below if the
driver remains present.

### Complete removal when the driver remains loaded

Deleting module files does not unload a module already running in the kernel.
If `lsmod | grep facetimehd` still returns output, the module is still loaded;
this alone does not tell you whether its files have been removed from disk.

1. **Close applications using the camera**, including Cheese, browser video
   calls, and conferencing applications. Identify remaining users of video
   devices, then close the relevant applications:

   ```bash
   sudo fuser -v /dev/video*
   sudo rmmod facetimehd
   sudo modprobe -r facetimehd
   lsmod | grep '^facetimehd '
   ```

   The final command should produce no output. If unloading reports that the
   module is in use, do not force removal. Complete the disk cleanup below and
   reboot to clear the loaded module.

2. **Remove every registered FaceTime HD DKMS version**:

   ```bash
   dkms status
   ```

   For each `facetimehd/VERSION` entry, remove that exact version from all kernels.
   For example, if the output lists `facetimehd/0.7.0.1`, run:

   ```bash
   sudo dkms remove facetimehd/0.7.0.1 --all
   ```

   Repeat for any other listed FaceTime HD versions, including `0.1` if present.
   If DKMS is no longer installed, skip this step and inspect the leftover files
   below. If DKMS removal fails, resolve the error before deleting its source.

3. **Inspect and remove leftover driver files and firmware**:

   ```bash
   sudo find /usr/src /var/lib/dkms -maxdepth 1 -name 'facetimehd*' -print
   sudo find /lib/modules -type f \( -name 'facetimehd.ko*' -o -name 'bcwc_pcie.ko*' \) -print
   ```

   Remove the installer source directory and camera firmware:

   ```bash
   sudo rm -rf /usr/src/facetimehd-driver /lib/firmware/facetimehd
   ```

   Remove any other FaceTime HD source or DKMS directories found above by their
   exact paths, after confirming they belong to this driver. If a distribution
   package owns any remaining files (`dpkg -S /path/to/file`), remove that package
   with `sudo apt purge PACKAGE_NAME` first to prevent it reinstalling the driver.
   Delete remaining manually installed module files:

   ```bash
   sudo find /lib/modules -type f \( -name 'facetimehd.ko*' -o -name 'bcwc_pcie.ko*' \) -delete
   ```

4. **Remove explicit startup configuration**. Find references to the driver:

   ```bash
   sudo grep -RnsE 'facetimehd|bcwc_pcie' \
     /etc/modules /etc/modules-load.d /etc/modprobe.d \
     /etc/initramfs-tools /etc/systemd/system \
     /etc/systemd/system-sleep /usr/lib/systemd/system-sleep 2>/dev/null
   ```

   Remove FaceTime HD load entries and any custom camera service or sleep hook
   you previously added. Edit shared files to remove only the relevant lines;
   delete a whole file only if it is dedicated to this driver. If you remove a
   custom systemd unit, disable it first and run `sudo systemctl daemon-reload`
   afterward.

5. **Refresh module indexes and boot images, then reboot**:

   ```bash
   for module_dir in /lib/modules/*; do
       [ -d "$module_dir" ] || continue
       sudo depmod -a "${module_dir##*/}"
   done
   sudo update-initramfs -u -k all
   sudo reboot
   ```

6. **Verify after reboot**:

   ```bash
   lsmod | grep '^facetimehd '
   dkms status
   modinfo facetimehd
   sudo find /lib/modules \( -name 'facetimehd.ko*' -o -name 'bcwc_pcie.ko*' \) -print
   ```

   Expected results: no loaded `facetimehd` module, no FaceTime HD entry in DKMS,
   no remaining module files, and a “Module facetimehd not found” error from
   `modinfo`. Skip `dkms status` if DKMS is no longer installed. The built-in
   camera will be unavailable until its driver and firmware are reinstalled.

---

## How It Works

The installer automates these steps:

1. **Install dependencies**: Ensures build tools and kernel headers are available
2. **Clone driver source**: Downloads the `facetimehd` driver repository
3. **Register with DKMS**: Enables automatic rebuilds on kernel updates
4. **Build kernel module**: Compiles the driver for your current kernel
5. **Extract firmware**: Downloads and installs Apple's proprietary camera firmware to `/lib/firmware/facetimehd/`
6. **Load driver**: Inserts the `bcwc_pcie` kernel module

DKMS (Dynamic Kernel Module Support) ensures the driver rebuilds automatically whenever you update your kernel, eliminating manual maintenance.

---

## Project Structure

```
facetimehd-ubuntu-macbook/
├── scripts/
│   ├── install.sh          # Main installation script
│   ├── uninstall.sh        # Removal script
│   └── power-tune.sh       # Optional power optimization
├── docs/
│   ├── TROUBLESHOOTING.md  # Detailed troubleshooting guide
│   └── POWER.md            # Power management documentation
├── dkms.conf               # DKMS configuration
├── README.md               # This file
├── CONTRIBUTING.md         # Contribution guidelines
├── CHANGELOG.md            # Version history
└── LICENSE                 # MIT License
```

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Ways to help:

- Report bugs or compatibility issues
- Test on different MacBook models
- Improve documentation
- Submit patches or enhancements

---

## Credits

This project builds upon excellent work from the open-source community:

- **Driver**: [patjak/facetimehd](https://github.com/patjak/facetimehd) – Reverse-engineered FaceTime HD driver
- **Firmware**: [patjak/facetimehd-firmware](https://github.com/patjak/facetimehd-firmware) – FacetimeHD firmware download and extraction tool
- **Power management**: [TLP](https://linrunner.de/tlp/) – Advanced power management for Linux
- **Linux camera stack**: V4L2, PipeWire, GStreamer, GNOME

This installer simply automates and packages their work into an easy-to-use tool.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Support

If you encounter issues:

1. Check the [troubleshooting guide](docs/TROUBLESHOOTING.md)
2. Search [existing issues](https://github.com/godwill1224/facetimehd-ubuntu-macbook/issues)
3. Open a [new issue](https://github.com/godwill1224/facetimehd-ubuntu-macbook/issues/new) with:
   - MacBook model (`sudo dmidecode -s system-product-name`)
   - Ubuntu version (`lsb_release -a`)
   - Kernel version (`uname -r`)
   - Output of `dkms status` and `lsmod | grep facetimehd`

---

**Made with ❤️ for the Linux + MacBook community**
