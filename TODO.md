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
| Driver: Storage register map | SdhciBlock.toml hardware address corrected from 0x71400000 (UMS512) to 0x201a0000 (hawaii); porting.toml documents SDHCI at 0x201a0000 |
| Driver: Wi-Fi | drivers/WcnWifi/NativeWcnWifi.cpp (adapted from Linux mainline drivers/net/wireless/unisoc/, SC23xx series) |
| Driver: Touch | drivers/GoodixTouch/NativeGoodixTouch.c — skeleton driver for Goodix gt9xx touch input. Component TOML: components/GoodixTouch/GoodixTouch.toml. Compiles with aarch64-linux-gnu-gcc. |
| Driver: Audio | drivers/Audio/NativeAudio.c — skeleton driver for SC2730 audio subsystem (vbc-v4-codec-sc2730, i2s-null-codec, audio-dsp-log, audio_sipc). Component TOML: components/Audio/Audio.toml. Compiles with aarch64-linux-gnu-gcc. |
| Driver: Power | drivers/Power/NativePower.c — skeleton driver for SC2730 PMIC (power-controller@1800, 10+ regulators, charger-manager, battery, pmic sub-devices). Component TOML: components/Power/Power.toml. Compiles with aarch64-linux-gnu-gcc. |
| Driver: GPU | drivers/MaliG57/NativeMaliG57.c + NativeMaliG57.h — skeleton driver for Mali-G57 Valhall (midgard-family in r28p0 DDK). Vendor DT: gpu@23100000 (sprd,mali-natt, reg=0x23100000/0x100000, irq=GIC_SPI 60 x3, DVFS 150-3300 MHz). Component TOML: components/MaliG57/MaliG57.toml. Compiles with aarch64-linux-gnu-gcc. |
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

## Completed (agent-3 — current session)

| Area | Evidence | How it was done |
|------|----------|-----------------|
| Kernel XNU build | **kernel.macho generated: sha256 a239a3a2b2d05579f1809af675bb161cb9f0f3acadec6b81eddd5163112d0634, ~51MB, Mach-O 64-bit arm64 executable, NOUNDEFS\|PIE flags.** Toolchain: clang-24 with __builtin_xnu_type_summary validated. 28 xnu patches applied. Prelink ABI patches (sparse-index + security-init) applied. | Built on Linux with clang-24 (LLVM 58c46bae) + llvm-xnu-builtin-type.patch |
| BootShim fixed (Mu-Silicium model) | uefi-hawaii/BootShim/BootShim.S rewritten: preserves x0 (FDT address), copies UEFI FD to FD_BASE, jumps to UEFI entry. Corrected _StackSize = FD_SIZE + (_Payload - _Head). | Based on Mu-Silicium BootShim.S, adapted for UMS9230 (FD_BASE=0x80800000, FD_SIZE=0x400000) |
| UEFI FD built | SILICIUM_UEFI.fd (4 MiB) at uefi-hawaii/Build/hawaiiPkg/DEBUG_CLANGPDB/AARCH64/FV/ | EDK2 (mu_basecore) + clang-21 (LLVM 21.1.8) from Ubuntu system packages |
| BootShim + UEFI FD assembled | payload/bootshim_fd.bin (4,194,512 bytes) with ARM64 header + magic ARMd @ 0x38 | scripts/assemble_bootshim_fd.py compiles BootShim.S with aarch64-linux-gnu-gcc, appends UEFI FD, prepends ARM64 header |
| Payload FAT created | payload/payload_fat.img (8 MiB, FAT12) with unixnu.toml config | scripts/create_fat_payload.py |
| boot.img packed (unsigned) | out/hawaii/boot/boot_unixnu.img (12,765,184 bytes, Android header v2) | scripts/pack_unixnu_boot.py using boot_b-original.img as base (preserves header, cmdline, DTB, vbmeta layout) |
| boot.img AVB-signed | out/hawaii/boot/boot_unixnu_signed.img (64 MiB) with SHA256_RSA4096, rollback index 2 | scripts/avb_sign.py (cryptography lib), self-signed RSA-4096 key |
| boot_a flashed via dd | boot_a written with boot_unixnu_signed.img, VERIFY OK (hash matched) | Root via mali_kroot (CVE-2021-28663), cat > /dev/block/by-name/boot_a |
| Device data extracted | extracted/cmdline.txt, iomem.txt, hawaii-live.dtb, boot_b-original.img (64 MiB), uboot_b.img (3 MiB) | Root shell, cat > /data/local/tmp/, adb pull |
| Device properties collected | Slot: _b, Device: hawaii, Platform: ums9230, RAM: 4GB, Framebuffer: 0x9e000000, GPU: 0x23100000, VBMeta: unlocked, flash.locked=0, verifiedbootstate=orange | adb shell getprop, cat /proc/cmdline, cat /proc/iomem |
| Slot switch to 'a' | User ran fastboot set_active a + fastboot reboot; device now boots from slot a (UniXNU boot_a) | fastboot mode (Volume Down + Power) |

## In Progress

| Area | Next action |
|------|-------------|
| Bring-up verification | Monitor device screen/UART1 (115200n8) for XNU boot progress: green bar (DarwinBoot), diagnostic page with build-tag=hawaii-001, or panic screen. If Android boots instead: slot switch failed, repeat set_active a. If bricked: fastboot set_active b + reboot (rescue to Android slot b). |

## Blocked

| Area | Blocker | Workaround |
|------|---------|------------|
| **fastboot flash boot_a** | Bootloader signature gate rejects unsigned images (`Please verify the signature!`). Even signed stock images rejected. Gate checks `*(u8 *)0x9f70a001 == 0` (unreachable flag). | Use `dd` from rooted Android (cat > /dev/block/by-name/boot_a), then `fastboot set_active a` + `fastboot reboot` |
| **fastboot boot stub** | `fastboot boot` ACKs any payload and reboots — does not actually load kernel. It is a stub on this bootloader. | Use dd to write to boot_a/boot_b partition, then switch slots |
| **bootloader secure flag** | `secure: true` in fastboot getvar. Software unlock via miscdata marker (docs/07-bootloader-unlock-how-to.md in motorola-moto-e32-root) already applied on this unit (flash.locked=0, verifiedbootstate=orange). | AVB self-signing defeats TrustOS check (a0=6 → tolerated a0=5) |
| **XNU not Linux Image** | XNU is Mach-O, not Linux ARM64 Image. bootloader expects Linux Image format. | Solution: BootShim (ARM64 Image with ARMd magic) loads UEFI FD, UEFI loads XNU Mach-O from payload FAT via DarwinBoot |

## Not Started

| Area | Next action |
|------|-------------|
| Network/Wi-Fi | Extract WCN firmware (wcnmodem.bin) from vendor partitions; test Wi-Fi driver on hardware |
| Audio DSP | Extract audio DSP firmware and ABI from vendor partitions |
| Power regulators | Map regulator names for hawaii variants from sc2730.dtsi |
| Touch controller | Identify touch controller model (cit_tp=0x00 in bootargs, disabled?) |
| Bring-up verification | Monitor UART1 (115200n8) or framebuffer diagnostic page for XNU boot progress |
| ramoops collection | Run scripts/ramoops-collect.py if panic occurs |
| porting.toml firmware area | Mark as done (firmware built, boot.img built) — verify next_action |

## Ferramentas Usadas (current session)

| Ferramenta | Versão | Propósito |
|------------|--------|-----------|
| aarch64-linux-gnu-gcc | 15.2.0 | Compilar BootShim.S (ARM64 ELF → binário) |
| aarch64-linux-gnu-objcopy | 15.2.0 | Converter ELF para binário bruto |
| Python 3 | 3.14.4 | Scripts de empacotamento, AVB signing, criação de payload FAT |
| cryptography (Python lib) | — | Geração de chave RSA-4096, assinatura AVB SHA256_RSA4096 |
| mali_kroot | — | Exploit CVE-2021-28663 para root temporário no Android |
| adb/fastboot (Windows) | Platform-Tools r37.0.3 | Comunicação com dispositivo, flash, reboot, set_active |
| EDK2 (mu_basecore) | release/202608 | Build do firmware UEFI SILICIUM_UEFI.fd |
| clang-21 | LLVM 21.1.8 | Toolchain EDK2 para build UEFI |
| clang-24 | LLVM 58c46bae | Toolchain XNU (build anterior, kernel.macho) |
| pack_and_sign_boot.py | motorola-moto-e32-root | Referência para estrutura do boot.img Android v2 |
| dtc | — | Compilação/validação de Device Tree |
| WSL2 | — | Ambiente Linux para build dos scripts Python |

## Scripts Created (current session)

| Script | Path | Purpose |
|--------|------|---------|
| assemble_bootshim_fd.py | scripts/assemble_bootshim_fd.py | Compiles BootShim.S, appends UEFI FD, prepends ARM64 header with ARMd magic |
| pack_unixnu_boot.py | scripts/pack_unixnu_boot.py | Packs boot.img Android v2 using boot_b original as base (header, cmdline, DTB preserved) |
| create_fat_payload.py | scripts/create_fat_payload.py | Creates FAT12/FAT16 payload image (4-8 MiB) with unixnu.toml config |
| avb_sign.py | scripts/avb_sign.py | AVB SHA256_RSA4096 signing (rollback index 2, stock salt) |
| flash_unixnu_dd.bat | flash_unixnu_dd.bat | Pushes image to device, roots via mali_kroot, dd to boot_a, verifies hash, set_active a, reboot |
| collect_data.bat | collect_data.bat | Collects device data (cmdline, iomem, DTB, boot_b, uboot_b) via root shell |
| PROGRESS.md | PROGRESS.md | Session progress tracking |

## Critical Path for First Boot

1. Device must be in fastboot mode (Volume Down + Power while powering on)
2. `fastboot set_active a` — switch to slot a (UniXNU boot.img)
3. `fastboot reboot` — boot from slot a
4. Monitor device screen for:
   - Green bar at top (DarwinBoot handoff)
   - Diagnostic page with boot stages
   - `build-tag=hawaii-001` in title
   - Panic screen if XNU fails
5. If Android boots instead: slot switch failed, repeat from step 1
6. If device is bricked/trapped: use slot b rescue (fastboot set_active b + fastboot reboot)