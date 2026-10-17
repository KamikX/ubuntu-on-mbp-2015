# Ubuntu on MacBook Pro 2015

This project collects guides, scripts, and configurations for running Ubuntu
on a 2015 MacBook Pro (MacBookPro11,4). It focuses on enabling hardware support,
tuning audio, and optimizing power consumption and system responsiveness.
It serves as a record of changes and a practical reference for installation
and system maintenance.

## Project Contents

- **FaceTime HD camera** – [camera installation and verification guide](facetimehd/docs/INSTALL.md),
  including the installer fixes required before running it. Related scripts
  and documentation are in [`facetimehd/`](facetimehd/).
- **Cirrus Logic CS4208 audio** – reference material, configurations, and audio
  tuning experiments in [`sound-driver-cs4208/`](sound-driver-cs4208/README.md).
- **Power consumption and performance** – [optimization documentation](power-optimization/README.md)
  covering CPU management settings, change verification, and rollback steps.

The system report below records the device's reference configuration.

## System Details Report

---

### Report details

#### Hardware Information:

- **Hardware Model:** Apple Inc. MacBookPro11,4
- **Memory:** 16.0 GiB
- **Processor:** Intel® Core™ i7-4770HQ × 8
- **Graphics:** Intel® Iris® Pro Graphics P5200 (HSW GT3)
- **Disk Capacity:** 1.0 TB

#### Software Information:

- **Firmware Version:** 489.0.0.0.0
- **OS Name:** Ubuntu 26.04.1 LTS
- **OS Build:** (null)
- **OS Type:** 64-bit
- **GNOME Version:** 50
- **Windowing System:** Wayland
- **Kernel Version:** Linux 7.0.0-38-generic
