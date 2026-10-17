#!/usr/bin/env bash
#
# FaceTime HD Camera Driver Installer
# Installs the bcwc_pcie/facetimehd driver for Apple FaceTime HD cameras on Linux
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (use sudo)"
    exit 1
fi

print_info "Starting FaceTime HD camera driver installation..."

# Update package list
print_info "Updating package list..."
apt update

# Install required dependencies
print_info "Installing build dependencies..."
apt install -y \
    dkms \
    git \
    curl \
    xz-utils \
    cpio \
    build-essential \
    linux-headers-$(uname -r) \
    v4l-utils \
    kmod

# Define working directory
WORKDIR="/usr/src/facetimehd-driver"
FIRMWARE_REPO="https://github.com/patjak/facetimehd-firmware.git"
FIRMWARE_DIR="/lib/firmware/facetimehd"

# Clone driver source if not already present
if [ ! -d "$WORKDIR" ]; then
    print_info "Cloning FaceTime HD driver source..."
    git clone https://github.com/patjak/facetimehd.git "$WORKDIR"
else
    print_warn "Driver source already exists at $WORKDIR"
    print_info "Pulling latest changes..."
    cd "$WORKDIR"
    git pull || true
fi

# Build and install driver with DKMS
print_info "Building driver with DKMS..."
cd "$WORKDIR"

# Clean previous builds
make clean || true

# Build and register with DKMS
#if ! make dkms; then
#   print_error "Driver build failed"
#   print_error "Check that kernel headers are installed: linux-headers-$(uname -r)"
#   exit 1
#fi

# Build and register with DKMS
sudo dkms remove facetimehd/0.7.0.1 --all 2>/dev/null || true
sudo dkms add .
if ! sudo dkms install facetimehd/0.7.0.1; then
    print_error "Driver build failed via DKMS"
    exit 1
fi


# Download and extract Apple's firmware using the upstream extraction tool.
print_info "Cloning FaceTime HD firmware extraction tools..."
FIRMWARE_WORKDIR="$(mktemp -d /tmp/facetimehd-firmware.XXXXXX)"
trap 'rm -rf -- "$FIRMWARE_WORKDIR"' EXIT

if ! git clone --depth 1 "$FIRMWARE_REPO" "$FIRMWARE_WORKDIR"; then
    print_error "Failed to clone firmware extraction tools"
    exit 1
fi

print_info "Downloading and extracting Apple camera firmware..."
if ! make -C "$FIRMWARE_WORKDIR"; then
    print_error "Failed to download or extract firmware"
    exit 1
fi

if [ ! -s "$FIRMWARE_WORKDIR/firmware.bin" ]; then
    print_error "Firmware extraction did not produce a non-empty firmware.bin"
    exit 1
fi

# Reject error pages or unrecognized binaries before replacing system firmware.
# SHA-256 values from the upstream extract-firmware.sh (Apple firmware versions).
FIRMWARE_SHA256="$(sha256sum "$FIRMWARE_WORKDIR/firmware.bin")"
case "${FIRMWARE_SHA256%% *}" in
    e3e6034a67dfdaa27672dd547698bbc5b33f47f1fc7f5572a2fb68ea09d32d3d|\
    240ef2e991f1d089d8228ce11d92b66bfa4b3d7289ec4fee228b64a713024330)
        print_info "Apple camera firmware checksum verified"
        ;;
    *)
        print_error "Unrecognized firmware checksum; refusing to install"
        exit 1
        ;;
esac

# The upstream install target also copies any extracted sensor calibration files.
print_info "Installing firmware..."
if ! make -C "$FIRMWARE_WORKDIR" install FW_DIR="$FIRMWARE_DIR"; then
    print_error "Failed to install firmware"
    exit 1
fi

# Verify firmware installation
if [ ! -s "$FIRMWARE_DIR/firmware.bin" ]; then
    print_error "Firmware file not found at $FIRMWARE_DIR/firmware.bin"
    exit 1
fi

# Do not unload/reload the camera here: reinitialization can freeze the system,
# especially after a failed probe. Keep installation separate from activation.
print_warn "Driver activation skipped: live unload/reload can freeze this hardware."
print_warn "Installing the module does not verify that camera initialization works."

# Verify installation
print_info "Verifying installation..."

# Check DKMS status
if dkms status facetimehd | grep -q "installed"; then
    print_info "✓ DKMS module installed"
else
    print_warn "DKMS module may not be properly installed"
fi

# Check if module is loaded
if lsmod | grep -q facetimehd; then
    print_info "✓ Kernel module loaded"
else
    print_info "Kernel module is not loaded; activation was intentionally skipped"
fi

# Check for video device
if [ -e /dev/video0 ]; then
    print_info "✓ Camera device detected: /dev/video0"
else
    print_warn "No /dev/video0 detected; camera operation has not been verified"
fi

# Print completion message
echo ""
print_info "Driver and firmware installation complete; camera operation is not verified."
echo ""
echo "Next steps:"
echo "  1. Restart your computer to load the camera driver: sudo reboot"
echo "  2. After restarting, test the camera: v4l2-ctl --list-devices"
echo "  3. If the camera does not work, inspect the kernel logs:"
echo "     sudo journalctl -k -b | grep -i facetimehd"
echo "  4. If loading previously froze the system, inspect the previous boot logs:"
echo "     sudo journalctl -k -b -1 | grep -Ei 'facetimehd|panic|Oops|lockup'"
echo "     For recovery, add module_blacklist=facetimehd to the GRUB kernel command line."
echo ""
echo "Optional:"
echo "  - Run power optimization: sudo ./scripts/power-tune.sh"
echo "  - See troubleshooting: docs/TROUBLESHOOTING.md"
echo ""
