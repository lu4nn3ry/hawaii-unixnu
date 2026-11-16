# TODO — hawaii-unixnu (Moto E32 / UMS9230 / T606)

Porting status following [UniXNU porting documentation](https://unixnu.com/porting/).
Tracked in `docs/porting.toml`; this file is a human-readable summary.

## Completed

| Area | Evidence |
|------|----------|
| Device repository skeleton | `board.toml`, `porting.toml`, `feeds.toml`, `README.md`, `AGENTS.md`, `.gitignore`, `local.toml.example` |
| SoC common support | `soc/UniXNU-ums9230-common/` with `soc.toml`, `configs/ums9230.config`, `dts/ums9230.dtsi` |
| Device tree | `dts/hawaii.dts` (board DTS, includes `ums9230.dtsi`) |
| Kernel defconfig | `configs/hawaii_defconfig` (ARM64, DT platform, ARM CPU, native timer, PAN) |
| UEFI firmware skeleton | `uefi-hawaii/` with BootShim, hawaii.dsc/fdf, UMS9230Pkg, hawaii.toml, mkbootimg.py |
| Build resolution | `./unixnu defconfig`, `fetch`, `status`, `tree` all resolve 5 official components (ArmDTPlatform, ArmCpu, SoftwareAES, XnuPrelink, DarwinBoot) |
| Driver: Storage | `drivers/SdhciBlock/NativeSdhciBlock.cpp` (adapted from `woshimaniubi8/unixnu-eebbk-a2_x2-ums512`, UMS512/T610 same family) |
| Driver: Wi-Fi | `drivers/WcnWifi/NativeWcnWifi.cpp` (adapted from Linux mainline `drivers/net/wireless/unisoc/`, SC23xx series) |
| Component TOMLs | `components/SdhciBlock/`, `components/WcnWifi/`, `components/MaliG57/`, `components/GoodixTouch/` |
| DTC fallback | `scripts/dtc-fallback.py` (Python fallback when `dtc` unavailable) |
| Packaging script | `scripts/package.sh` |
| CI workflows | `.github/workflows/porting-record.yml`, `.github/workflows/package.yml` |
| Vendor DTB captured | `dts/fdt_from_device.bin` (pulled from `/sys/firmware/fdt` via adb) |

## In Progress

| Area | Next action |
|------|-------------|
| Firmware UEFI | Verify `FD_BASE`/`FD_SIZE` from vendor `uboot.bin`; build FD on host with EDK2; fastboot boot CI boot.img on hardware, capture UART1/ramoops |
| CPU/Memory | Decompile vendor `boot_b` DTB, extract cpu/gic/timer/memory nodes, verify against `ums9230.dtsi` |
| Packaging | Parse `hawaii` `boot_b` header and fill exact offsets in `board.toml` `[bootimg]` |
| Diagnostics | Prepare UART access and ramoops collection script before first flash attempt |

## Not Started

| Area | Next action |
|------|-------------|
| Display | Read panel timing from vendor kernel DTB; confirm framebuffer state on hardware |
| Input | Search UniXNU repos for touch driver (Goodix gt9xx, etc.); extract touch node and GPIO/interrupt wiring from vendor DTB |
| GPU | Inventory Mali-G57 model and firmware from vendor DTB/kernel; clone `Ken-u/Mali` as reference; write Mali-G57 CSF driver with correct registers and firmware path |
| Network | Extract WCN model and firmware files from vendor `super`/`vendor` partitions; test Wi-Fi driver on hardware |
| Audio | Inventory audio DSP firmware and codec wiring |
| Power | Extract PMIC/charger nodes and regulator names from vendor DTB |

## Build Commands

```bash
# From the UniXNU core checkout
DEVICE_DIR=../hawaii-unixnu
DEFCONFIG=hawaii_defconfig

./unixnu defconfig "$DEFCONFIG" -D "$DEVICE_DIR"
./unixnu fetch -D "$DEVICE_DIR"
./unixnu status --json -D "$DEVICE_DIR"
./unixnu tree -D "$DEVICE_DIR"
python3 scripts/porting-record.py check --device "$DEVICE_DIR"

# Device tree compilation (requires dtc)
dtc -I dts -O dtb -i soc/dts -o /tmp/hawaii.dtb dts/hawaii.dtd

# Firmware build (requires EDK2 toolchain)
./unixnu build firmware --uefi ../uefi-hawaii

# Payload and boot image
./unixnu build payload --unique-chip-id <hex> --trust-cache <file> --data-ramdisk <seed>
./unixnu bootimg --uefi ../uefi-hawaii --dtb /path/to/firmware.dtb
```

## Device Facts (measured on hardware)

| Property | Value |
|----------|-------|
| SoC | Unisoc UMS9230 / Tiger T606 (`qogirl6`) |
| CPU | 2× Cortex-A75 + 6× Cortex-A55 @ 1.6 GHz |
| GPU | Mali-G57 (Valhall, JM-based, DDK r28p0) |
| RAM | ~3.5 GiB |
| Bootloader | Unlocked (`flash.locked=0`) |
| Android | 11, VNDK 30, Treble enabled |
| Partitions | Virtual A/B, dynamic `super` |
| UART | `ttyS1` @ 115200n8 |
| Boot image | header v2, pagesize 2048, DTB inside boot |
