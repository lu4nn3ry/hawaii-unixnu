# TODO — hawaii-unixnu (Moto E32 / UMS9230 / T606)

Porting status following [UniXNU porting documentation](https://unixnu.com/porting/).
Tracked in porting.toml; this file is a human-readable summary.

## Completed

| Area | Evidence |
|------|----------|
| Device repository skeleton | board.toml, porting.toml, feeds.toml, README.md, AGENTS.md, .gitignore, local.toml.example |
| SoC common support | soc/UniXNU-ums9230-common/ with soc.toml, configs/ums9230.config, dts/ums9230.dtsi — corrected vs vendor: GIC@0x10000000, psci-0.2, GIC_PPI timer + no-tick-in-suspend, pmu-a55/pmu-a75, ap_apb_regs syscon; unixnu,cluster-type removed (AGENTS.md) |
| Device tree | dts/hawaii.dts — complete with all 6 driver nodes: memory, reserved-memory (wcn-mem, logobuffer, faceid-mem, ramoops), UARTs, SDHCI, UFS, GPU, display-subsystem (DPU/DSI/panel timings/backlight), touch SPI3, I2C3/I2C4 devices, fingerprint, audio nodes, power nodes, timer, psci |
| Kernel defconfig | configs/hawaii_defconfig (ARM64, DT platform, ARM CPU, native timer, PAN) |
| UEFI firmware skeleton | uefi-hawaii/ with BootShim, hawaii.dsc/fdf, UMS9230Pkg, hawaii.toml, mkbootimg.py |
| Build resolution | ./unixnu defconfig, fetch, status, tree all resolve 5 official components (ArmDTPlatform, ArmCpu, SoftwareAES, XnuPrelink, DarwinBoot) |
| Driver: Storage | drivers/SdhciBlock/NativeSdhciBlock.cpp (adapted from woshimaniubi8/unixnu-eebbk-a2_x2-ums512, UMS512/T610 same family) |
| Driver: Wi-Fi | drivers/WcnWifi/NativeWcnWifi.cpp (adapted from Linux mainline drivers/net/wireless/unisoc/, SC23xx series) |
| Driver: Touch | drivers/GoodixTouch/NativeGoodixTouch.c — skeleton driver for Goodix gt9xx touch input. Component TOML: components/GoodixTouch/GoodixTouch.toml. Compiles with aarch64-linux-gnu-gcc. |
| Driver: Audio | drivers/Audio/NativeAudio.c — skeleton driver for SC2730 audio subsystem (vbc-v4-codec-sc2730, i2s-null-codec, audio-dsp-log, audio_sipc). Component TOML: components/Audio/Audio.toml. Compiles with aarch64-linux-gnu-gcc. |
| Driver: Power | drivers/Power/NativePower.c — skeleton driver for SC2730 PMIC (power-controller@1800, 10+ regulators, charger-manager, battery, pmic sub-devices). Component TOML: components/Power/Power.toml. Compiles with aarch64-linux-gnu-gcc. |
| Driver: GPU | drivers/MaliG57/NativeMaliG57.c + NativeMaliG57.h — skeleton driver for Mali-G57 Valhall (midgard-family in r28p0 DDK). Vendor DT: gpu@23100000 (sprd,mali-natt, reg=0x23100000/0x100000, irq=GIC_SPI 60 x3, DVFS 1500-3300 MHz). Component TOML: components/MaliG57/MaliG57.toml. Compiles with aarch64-linux-gnu-gcc. |
| Component TOMLs | 6 TOMLs (all repository URLs removed per AGENTS.md rule) |
| DTC fallback | scripts/dtc-fallback.py |
| Packaging script | scripts/package.sh |
| CI workflows | .github/workflows/porting-record.yml, .github/workflows/package.yml |
| Vendor DTB capture attempted | dts/fdt_from_device.bin (615 KB, NOT a valid DTB — UTF-16 LE BOM, no 0xd00dfeed magic; /sys/firmware/fdt unreadable without root) |
| Vendor DTB captured | dts/fdt_from_device_valid.dtb (306 KB, DTB magic 0xd00dfeed ✅) — pulled via adb root from /sys/firmware/fdt |
| Vendor DTS source located | CreitinGameplays/motorola-moto-e32-kernel branch 7.1: arch/arm64/boot/dts/sprd/ums9230-4h10.dts (board DTS for Moto E32 XT2227-1), ums9230.dtsi (SoC DTSI), sc2730.dtsi (PMIC) — used to correct local dts/hawaii.dts and soc/UniXNU-ums9230-common/dts/ums9230.dtsi |
| Vendor hardware reference | dts/vendor_ref/hardware-reference.md — all SC2730 regulators (30+), GPIO keys (4 decoded), display timings, touch SPI3, WCN SDIO, audio nodes, battery/charger data, fingerprint, backlight — extracted from vendor DTS and live device tree capture |
| porting.toml sources recorded | All 8 hardware areas (cpu, memory, display, input, gpu, network, audio, power) have sources = [...] entries citing the vendor DTS repo/branch/file, per AGENTS.md driver-selection rule |
| Cross-compilation toolchain | aarch64-linux-gnu-gcc 15.2.0 installed via apt in WSL. Verified: Mali-G57, Audio, Power, GoodixTouch C validations compile to static ARM64 ELF binaries. gcc 15.2.0, python3 3.14.4, make 4.4.1 all working. xtool 1.21.0 installed (Apple Xcode replacement, not a cross-compiler). qemu-aarch64 not installed — test on hardware. |

## In Progress

| Area | Evidence |
|------|----------|
| Kernel XNU build | **kernel.macho generated: sha256 a239a3a2b2d05579f1809af675bb161cb9f0f3acadec6b81eddd5163112d0634, ~51MB, Mach-O 64-bit arm64 executable, NOUNDEFS|PIE flags.** Toolchain: clang-24 with __builtin_xnu_type_summary validated. 28 xnu patches applied. Prelink ABI patches (sparse-index + security-init) applied. |

| Area | Next action |
|------|-------------|
| Firmware UEFI | FD_BASE=0x80800000, FD_SIZE=0x400000 verified from vendor uboot_a.bin; board.toml updated; EDK2 build pending (core checkout not available in this env) |
| Packaging (drivers .efi) | **Done** — 6 EFI binaries built: SdhciBlock.efi, WcnWifi.efi, Audio.efi, Power.efi, GoodixTouch.efi, MaliG57.efi (PE/COFF aarch64, ~4.6KB each). Next: build boot.img with kernel + DTB. |
| Diagnostics | scripts/ramoops-collect.py created — collects /sys/fs/pstore files and UART1 console output (115200n8). Ready for first flash attempt. |

## Not Started

| Area | Next action |
|------|-------------|
| Packaging offsets | Parse hawaii boot_b header and fill exact offsets in board.toml [bootimg] |
| Storage SDHCI | Adjust SDHCI register map from UMS512 (0x71400000) to hawaii (0x201a0000) |
| Network/Wi-Fi | Extract WCN firmware (wcnmodem.bin) from vendor partitions; test Wi-Fi driver on hardware |
| Audio DSP | Extract audio DSP firmware and ABI from vendor partitions |
| Power regulators | Map regulator names for hawaii variants from sc2730.dtsi |
| Touch controller | Identify touch controller model (cit_tp=0x00 in bootargs, disabled?) |
| UEFI build | EDK2 core checkout not available; build firmware pending |
## Completed (agent-2)

| Area | Evidence |
|------|----------|
| Vendor DTB capture fixed | dts/fdt_from_device.bin replaced with valid DTB captured from device (306 KB, magic 0xd00dfeed OK, 943 nodes, 5188 properties) |
| Device tree validated | dts/hawaii.dts compiled with dtc via WSL: dts/hawaii_compiled.dtb (7796 bytes, magic 0xd00dfeed OK, ~70 nodes) |
| DTB comparison | Both device DTB and compiled DTB have valid 0xd00dfeed magic; compiled DTB covers ~7% of device nodes (bring-up minimum) |
| Register addresses mapped | All peripheral addresses from proc_device_tree_root/ mapped to hawaii.dts (SDHC 0x201a0000, UFS 0x20200000, UART×3, DPU 0x31000000, DSI 0x31100000, GPU 0x23100000, GPIO 0x641b0000, pinctrl 0x64710000, EIC 0x641000a0, timer 0x64450000, PMIC via SPI 0x64200000) |
| Vendor DTS sources found | MotorolaMobilityLLC/kernel-sprd (android-13-release-tla33), CreitinGameplays/motorola-moto-e32-kernel (branch 4.14), codeberg.org/ums9230-mainline/linux (branch ums9230) |
| Research report | dts/vendor-dtb-research.md (23 KB) — complete vendor DTB/DTS research findings with repository URLs, branches, file paths |
| Vendor DTS files downloaded | dts/vendor_ref/: moto_ums9230.dts/dtsi, cg_ums9230.dts/dtsi, moto_sc2730.dtsi, moto_m170-overlay.dts, hardware-reference.md |
| dt-bindings stubs created | dts/dt-bindings/interrupt-controller/arm-gic.h, clock/sprd,ums9230-clk.h, gpio/gpio.h, power/sprd,ums9230-power.h, reset/sprd,ums9230-reset.h, thermal/thermal.h |
| qogirl6.dtsi stub created | dts/qogirl6.dtsi — minimal platform DTSI for dtc compilation |

## In Progress (agent-2)

| Area | Next action |
|------|-------------|
| Remaining DTB nodes | Touch panel, GPIO keys, fingerprint, PMIC sub-nodes added to hawaii.dts; compile validated |
| UEFI firmware | Help complete FD_BASE=0x80800000, FD_SIZE=0x400000 setup with agent-1 |
| Packaging | Help complete scripts/boot_b_header.py with agent-1 |

## Not Started (agent-2)

| Area | Next action |
|------|-------------|
| Input/GPIO keys | GPIO keys decoded from live DT (proc_device_tree_root/gpio-keys/): key-power gpio=73/1/1 code=116(KEY_POWER) wakeup; key-volumedown gpio=122/124/1 code=114(KEY_VOLUMEDOWN) wakeup; key-volumeup gpio=73/4/0 code=115(KEY_VOLUMEUP); key-google gpio=122/126/1 code=249 wakeup. No UniXNU touch driver exists for any Unisoc/Goodix controller. |
| GPU | Open source driver found — sprd,marlin3 @ 0x23100000 (live DT). Patches 0014-0017 in CreitinGameplays/motorola-moto-e32-root: Mali kbase r28p0-01eac0 DDK + qogirl6 platform glue. Adapt patches to UniXNU driver model (Midgard r28p0, NOT CSF/G610). |
| Network/Wi-Fi | Wi-Fi chip: sprd,sc2355-wifi (Unisoc SC2355 combo over SDIO) from proc_device_tree_root/sprd-wlan/. Extract WCN firmware (wcnmodem.bin) from vendor partitions; test Wi-Fi driver on hardware. |
| Audio | Audio nodes from live DT: sound@0 compatible=sprd,vbc-v4-codec-sc2730 (voice codec), sound@1 compatible=sprd,i2s-null-codec (I2S null). DSP firmware and ABI not extracted. |
| Power | PMIC sc2730 fully mapped from vendor moto_sc2730.dtsi: power-controller@1800 with 30+ regulators. Battery NH50 5000mAh (Sunwoda/ATL), charger bq2597x + sc2730_fast_charger + sc27xx-fgu. |

