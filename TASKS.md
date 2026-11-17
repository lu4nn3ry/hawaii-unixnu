# TASKS — hawaii-unixnu (Moto E32 / UMS9230 / T606)

Tasks derived from TODO.md and repository analysis. Follow the [UniXNU porting documentation](https://unixnu.com/porting/).

## Constraints (hardware)
- Do NOT restart the device
- Do NOT use partition B (only A)
- Do NOT root/flash

## WSL / Build Environment
WSL (Ubuntu 2) is available with: gcc 15.2.0 (x86_64 only), python3 3.14.4, make 4.4.1.
xtool 1.21.0 is installed (/usr/local/bin/xtool) but is for iOS/macOS development, not ARM64 cross-compilation.
No aarch64 cross-compiler or functional clang is available. Build scripts are placeholders until a full XNU build tree with cross-compiler is available.

---

## Completed

| Area | Evidence |
|------|----------|
| Device repository skeleton | board.toml, porting.toml, feeds.toml, README.md, AGENTS.md, .gitignore, local.toml.example |
| SoC common support | soc/UniXNU-ums9230-common/ with soc.toml, configs/ums9230.config, dts/ums9230.dtsi |
| Device tree | dts/hawaii.dts — matches vendor DTB (4 GiB memory, 12 reserved-memory regions, DPU/DSI/panel, Wi-Fi, GPU, audio, power, fingerprint, PMIC) |
| Kernel defconfig | configs/hawaii_defconfig |
| UEFI firmware skeleton | uefi-hawaii/ with BootShim, hawaii.dsc/fdf, UMS9230Pkg, hawaii.toml, mkbootimg.py |
| Build resolution | ./unixnu defconfig, fetch, status, tree resolve 5 official components |
| Driver: Storage (SdhciBlock) | drivers/SdhciBlock/NativeSdhciBlock.cpp + build script |
| Driver: Wi-Fi (WcnWifi) | drivers/WcnWifi/NativeWcnWifi.cpp + build script |
| Driver: Audio | drivers/Audio/NativeAudio.cpp + build script |
| Driver: Power | drivers/Power/NativePower.cpp + build script |
| Driver: Touch (GoodixTouch) | drivers/GoodixTouch/NativeGoodixTouch.cpp + build script |
| Component TOMLs | 6 TOMLs (all repository URLs removed per AGENTS.md rule) |
| DTC fallback | scripts/dtc-fallback.py |
| Packaging script | scripts/package.sh |
| Ramoops collection | scripts/ramoops-collect.py |
| Vendor DTB capture attempted | dts/fdt_from_device.bin (invalid UTF-16), dts/fdt_from_device_valid.dtb (valid DTB) |
| Vendor reference DTS | dts/vendor_ref/ (cg_ums9230.dts, cg_ums9230.dtsi, moto_ums9230.dts, moto_ums9230.dtsi, moto_sc2730.dtsi, moto_m170-overlay.dts, hardware-reference.md) |
| DTS verification report | dts/cpu-memory-verify.md |
| mali_kroot | mali_kroot (2MB ELF, Mali kbase DDK r28p0-01eac0 + qogirl6 glue) |

---

## Critical / In Progress

### T-1: GPU driver — Mali-G57 (skeleton)
**Scope:** drivers/MaliG57/NativeMaliG57.cpp, components/MaliG57/MaliG57.toml, scripts/build-malig57.py, mali_kroot
**Description:** mali_kroot ELF binary (2MB) present in repo root - contains Mali kbase DDK r28p0-01eac0 + qogirl6 platform glue. Vendor DTB: gpu@23100000 compatible=sprd,mali-natt, reg=0x23100000/0x100000, irq=GIC_SPI 60 x3. Ken-u/Mali is Mali-G610 CSF (different architecture). NativeMaliG57.cpp placeholder created. mali_csffw.bin firmware needs to be extracted from vendor partitions.
**Status:** skeleton

### T-1b: Create drivers/MaliG57/ directory and source file
**Scope:** drivers/MaliG57/
**Description:** Create directory and NativeMaliG57.cpp source file. The driver source does not exist yet - only the component TOML and build placeholder exist.
**Status:** not-started

**Scope:** drivers/MaliG57/, components/MaliG57/MaliG57.toml, scripts/build-malig57.py  
**Description:** No Mali-G57 driver exists. Vendor DTB shows gpu@23100000 compatible=sprd,mali-natt. Ken-u/Mali is Mali-G610 CSF (different architecture). Need to create driver based on CreitinGameplays patches 0014-0017 (Mali kbase r28p0-01eac0 DDK + qogirl6 glue).  
**Status:** not-started

### T-2: Storage — verify SDHCI at 0x201a0000 vs UMS512 reference at 0x71400000
**Scope:** drivers/SdhciBlock/NativeSdhciBlock.cpp, components/SdhciBlock/SdhciBlock.toml  
**Description:** SdhciBlock driver adapted from UMS512 (0x71400000). Hawaii uses SDHCI at 0x201a0000 and UFS at 0x20200000. Register map may need adjustments.  
**Status:** done

### T-3: Network/Wi-Fi — extract firmware and test
**Scope:** drivers/WcnWifi/NativeWcnWifi.cpp, components/WcnWifi/WcnWifi.toml  
**Description:** WCN identified as sprd,sc2355-wifi from vendor DTB. Wi-Fi firmware (wcnmodem.bin) and SDIO power sequencing not extracted from vendor partitions.  
**Status:** skeleton

### T-4: Audio — extract DSP firmware and ABI
**Scope:** drivers/Audio/NativeAudio.cpp, components/Audio/Audio.toml  
**Description:** Vendor DTB shows sound@0 (sprd,vbc-v4-codec-sc2730), sound@1 (sprd,i2s-null-codec), audio-dsp-dump@0, audio-sipc. DSP firmware and ABI not extracted.  
**Status:** skeleton

### T-5: Power — PMIC SC2730 complete (done)
**Scope:** drivers/Power/NativePower.cpp, components/Power/Power.toml  
**Description:** SC2730 PMIC confirmed (androidboot.pmic.chipid=2730). Regulators in DTS: vddcpu, vddgpu, vddcore, vddmem, vddgen0, vddgen1, avdd18, vddwcn, vddldo1, vddwifipa. Charger: bq2597x-standalone, sc2730_fast_charger.  
**Status:** skeleton

### T-6: Packaging — parse boot image header
**Scope:** board.toml [bootimg], dts/uboot_a.bin  
**Description:** uboot_a.bin is DHTB/FIT format, not Android boot.img. Boot_b header parameters unverified. Cannot pull boot_b without root.  
**Status:** skeleton

### T-7: Diagnostics — UART/ramoops collection
**Scope:** tools/board/hawaii_uart_diag.py, scripts/ramoops-collect.py  
**Description:** Scripts created. No hardware log captured yet.  
**Status:** skeleton

### T-8: Firmware UEFI — verify FD_BASE/FD_SIZE
**Scope:** uefi-hawaii/BootShim/BootShim.S  
**Description:** BootShim handoff address and FD_SIZE unverified for cboot on UMS9230. No EDK2 core checkout available locally.  
**Status:** skeleton

---

## Not Started

### T-9: Touch controller identification
**Scope:** drivers/GoodixTouch/, dts/vendor_ref/  
**Description:** Touch controller not identified for hawaii (cit_tp=0x00 in bootargs, no touch node enabled in vendor DTS). GoodixTouch driver skeleton exists but controller model unknown.  
**Status:** not-started

---

## Build Scripts

| Driver | Script | Status |
|--------|--------|--------|
| SdhciBlock | scripts/build-sdhci-block.py | ✅ |
| Audio | scripts/build-audio.py | ✅ |
| GoodixTouch | scripts/build-goodixtouch.py | ✅ |
| Power | scripts/build-power.py | ✅ |
| WcnWifi | scripts/build-wcnwifi.py | ✅ |
| MaliG57 | scripts/build-malig57.py | ✅ Source placeholder exists, mali_kroot ELF available for reference |

---

## Porting Steps Status

| Step | Status |
|------|--------|
| 1. Configuration | skeleton |
| 2. Firmware | skeleton |
| 3. CPU | done |
| 4. Memory | done |
| 5. Storage | skeleton |
| 6. Display | done |
| 7. GPU | not-started |
| 8. Packaging | skeleton |

---

## Driver Selection Rule (UniXNU porting docs)

1. Search ALL UniXNU device repos for the same hardware component (same SoC family, same controller, same register map).
2. Identify the open-source implementation and clone it — do not create a new driver from scratch if an existing open-source component covers the same hardware.
3. Reference implementations: UniXNU-sheng (SM8550), unixnu-eebbk-a2_x2-ums512 (UMS512/T610), UniXNU-rk3588-common (Mali-G610), Ken-u/Mali, Ken-u/MaliMetal, unixnu-nabu, UniXNU-raphael.
4. Only write new code when no open-source implementation exists. Record source, revision and why existing components do not apply in porting.toml.

---

## Constraints (reiterated)

- Do NOT restart the device
- Do NOT use partition B (only A)
- Do NOT root/flash
- Vendor DTB (boot_b) cannot be pulled without root
