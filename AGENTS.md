# Agent instructions

This repository owns the Moto E32 (hawaii / XT2227-1) board port for UniXNU.
Board peripherals, firmware selection, partition layout, and power policy live
here; keep SoC operations in the shared soc support (ums9230-common) once it is
published.

Read these UniXNU pages before editing:

1. [Porting](https://unixnu.com/porting/)
2. [Device repositories](https://unixnu.com/porting/device-repository)
3. [Components](https://unixnu.com/reference/components)
4. [Device trees](https://unixnu.com/porting/device-tree)
5. [Driver matching](https://unixnu.com/drivers/device-tree-matching)
6. [Develop a driver](https://unixnu.com/porting/driver-development)

Rules specific to this repository:

- The target is Mach-O. Inline assembly goes through the Darwin assembler,
  where `;` starts a comment. Separate instructions with `"\n\t"` and check
  the object with `llvm-objdump --disassemble-symbols`.
- A node reaches the Apple device tree only with `unixnu,adt-name` and
  `status` other than `disabled`. Do not add `unixnu,cluster-type` or
  `virtual-timer-intid`; the working kernel runs without them.
- XNU patches apply with plain `git apply` in series order, after the ARM64
  series and before the OS and device series. Check new patches against a
  fresh XNU clone.
- Do not use observations from other Unisoc SoCs to decide UMS9230 behavior.
- Keep addresses, hostnames, accounts, and local paths out of this repository.
- `tools/board/` is host-side tooling shared by boards. Keep any board's USB ids, load addresses, boot flow, and
  payload out of it, and run `python3 tools/board/selftest.py` after editing it.

Driver selection rule (follow the UniXNU porting documentation exactly):

1. Before implementing any driver, search ALL UniXNU device repositories for
   the same hardware component (same SoC family, same controller, same
   register map).
2. Identify the open-source implementation and clone it - do not create a new
   driver from scratch if an existing open-source component covers the same
   hardware.
3. Reference implementations to inspect first:
   - `https://github.com/UniXNU/UniXNU-sheng` (SM8550, reference device)
   - `https://github.com/woshimaniubi8/unixnu-eebbk-a2_x2-ums512` (UMS512/T610, same Unisoc family - HAS SdhciBlock storage driver)
   - `https://github.com/Ken-u/UniXNU-rk3588-common` (Mali-G610 Valhall - closest to Mali-G57)
   - `https://github.com/Ken-u/Mali` (Mali-G610 CSF kernel driver for UniXNU)
   - `https://github.com/Ken-u/MaliMetal` (Metal frontend for Mali on UniXNU)
   - `https://github.com/Lux12138/unixnu-nabu` (Xiaomi Pad 5)
   - `https://github.com/JohnLeeeeeee678/UniXNU-raphael` (iOS 16.7.16 on SM8150)
4. Only write new code when no open-source implementation exists for the
   hardware. Record the source, revision and why existing components do not
   apply in `porting.toml`.

Research results (2026-11-16):

| Component | Existing implementation | Can adapt to T606/UMS9230? | Notes |
|-----------|------------------------|---------------------------|-------|
| Storage (SDHCI/eMMC) | `woshimaniubi8/unixnu-eebbk-a2_x2-ums512` `drivers/SdhciBlock` | YES - same Unisoc SDHCR11 at 0x71400000 | UMS512/T610 same family as UMS9230/T606 |
| GPU (Mali-G57 Valhall) | `Ken-u/Mali` (Mali-G610 CSF) | PARTIAL - same Valhall arch, different GPU_ID/registers | G610 product 7, G57 different product ID |
| GPU Metal frontend | `Ken-u/MaliMetal` | PARTIAL - same Valhall arch | PanVK + metal2vulkan bridge |
| Display (GOP/framebuffer) | `woshimaniubi8/unixnu-eebbk-a2_x2-ums512` BootShim.S | PARTIAL - DPU/DSI at 0x20300000/0x20400000 | Same Unisoc display block |
| Wi-Fi (WCN SDIO) | None found in UniXNU repos | NO - no open-source implementation | Needs new driver |
| Touch (Goodix gt9xx) | None found in UniXNU repos | NO - no open-source implementation | Needs new driver |

Linux kernel mainline for UMS9230/T606 (source for drivers):

| Source | Repository | Status | Notes |
|--------|-----------|--------|-------|
| ums9230-mainline Linux | `codeberg.org/ums9230-mainline/linux` branch `ums9230` | ACTIVE | UFS, DPU/DSI, PMIC sc2730, pinctrl, GPIO/EIC working |
| itel S681LN board port | `github.com/fahrulseptiana/s681ln-mainline` | ACTIVE | UMS9230/T616, same family as T606; boots to userspace |
| postmarketOS/Nura | `codeberg.org/ums9230-mainline` | ACTIVE | SoC support already in mainline |

Report commands, results, required local inputs, and hardware checkpoints.
Write concise English describing current behavior.

## Boot flow and debugging (learned 2026-11-17)

### Boot chain
1. Bootloader (cboot/U-Boot) loads boot.img kernel field to 0x80080000, jumps with x0 = FDT
2. BootShim (ARM64 Image, magic `ARMd` @ 0x38) copies UEFI FD (4 MB) to 0x80800000, branches to SEC
3. UEFI SEC: sets stack, publishes memory via MemoryMapLib, records FDT in HOB, loads PEI/DXE
4. DXE: CpuDxe, ArmGicDxe, TimerDxe, RamManagerDxe, DtPlatformDxe, SimpleFbDxe
5. BDS: UniXNUDxe registers Boot#### for UniXNU.efi, BDS starts the menu
6. DarwinBoot: loads XNU Mach-O from payload FAT, prepares ADT, exits boot services

### BootShim critical fixes
- **ARM64 header alignment**: `adr x1, _Payload` at 0x00 (code0), `b _Start` at 0x04 (code1),
  `text_offset` at 0x08, `image_size` at 0x10, `ARMd` magic at 0x38.
  Do NOT prepend a synthetic header — the BootShim already contains a valid ARM64 header.
  A synthetic zero header causes `UDF #0` at 0x00 → bootloop.
- **`.ltorg` before `_Payload`**: flushes the literal pool (FD_BASE/FD_SIZE) so it does not
  overlap the appended UEFI FD. Without it, `_Payload` points to the literal pool, not the FD.
- **No gzip**: `kernel_compression = "none"` in hawaii.toml. cboot expects a raw ARM64 Image.

### UEFI firmware build
- **Toolchain**: CLANGDWARF (not CLANGPDB). firmware.py modified to use CLANGDWARF.
  `CLANGDWARF_BIN=/usr/bin/` (system clang).
- **Dependencies**: mu_basecore + mu_plus (MsCorePkg/MsGraphicsPkg/PcBdsPkg) + mu_oem_sample.
  Symlink mu_plus and mu_oem_sample into the work tree for `{mu_plus}`/`{mu_oem_sample}` fields.
- **DSC/FDF structure**: follows bbkA2 reference (SEC in FVMAIN_COMPACT, DXE in FVMAIN,
  APRIORI.inc + DXE.inc includes, Common.fdf.inc).
- **MemoryMapLib**: board-specific, defines all memory regions (stack, heap, page tables, FD,
  DXE heap, FDT, initrd, framebuffer, ramoops, peripherals).
- **SerialPortLib**: RGB565 (16bpp) at 0x9e000000, UART1 at 0x200b0000 (115200n8).
  One-shot UART probe (20000 reads) — if TX_OVER never asserts, UART is marked dead.
  ramoops at 0xfff80000 (console) + 0xfffb0000 (dmesg mirror).
- **PlatformSecLib**: stage markers on panel — CYAN (0x07FF) = SEC assembly ran,
  MAGENTA (0xF81F) = SEC C code ran, text = SEC reached SerialPortInitialize.
  Without UART, the screen colour is the only diagnostic.
- **BringupDxe**: resets to Android (PSCI SYSTEM_RESET) at EndOfDxe so every test ends
  with a readable ramoops log instead of a black screen hang.

### Flash procedure (dd + slot switch)
1. `adb reboot bootloader` → `fastboot set_active b` → `fastboot reboot` (Android slot b)
2. Root via mali_kroot (CVE-2021-28663) in /data/local/tmp/
3. `adb push boot_unixnu_signed.img /data/local/tmp/`
4. `adb shell su -c 'dd if=/data/local/tmp/boot_unixnu.img of=/dev/block/by-name/boot_a bs=4M'`
5. Verify: `sha256sum /dev/block/by-name/boot_a` == host sha256
6. `adb reboot bootloader` → `fastboot set_active a` → `fastboot reboot`
7. Monitor: screen colour (cyan/magenta/text), ramoops after return to Android

### Bootloop diagnosis
- **No bootloop + black screen**: UEFI SEC is running but hung before EndOfDxe.
  PlatformSecLib stage markers tell you how far: black = BootShim/SEC entry fault,
  cyan = SEC assembly ran, magenta = SEC C ran.
- **Bootloop (restarts every ~5s)**: BootShim or early SEC fault → watchdog reset.
  Check ARM64 header alignment and `.ltorg` first.
- **Return to Android after ~15s**: BringupDxe fired successfully → UEFI reached EndOfDxe.
  Read ramoops from `/sys/fs/pstore/` in Android for the debug log.

### Key addresses (UMS9230 / hawaii)
- System RAM: 0x80000000-0x17fffefff (4 GiB)
- Kernel load: 0x80080000 (cboot), UEFI FD_BASE: 0x80800000, FD_SIZE: 0x400000
- UEFI stack: 0x80480000, SEC heap: 0x80680000, MMU PT: 0x80780000
- DXE heap: 0x80C00000-0x81FD0000, VarStore: 0x81FD0000, FDT: 0x82000000
- Framebuffer (logobuffer): 0x9e000000 (1600x720, RGB565)
- Ramoops: 0xfff80000 (console), 0xfffb0000 (dmesg)
- GIC: GICD 0x10000000, GICR 0x10040000
- UART1: 0x200b0000 (115200n8)
- SDHCI: 0x201a0000, DPU: 0x31000000, DSI: 0x31100000
- GPIO: 0x641b0000, EIC: 0x641000a0, PMIC SPI: 0x64200000
- Timer: 0x64470000, pinctrl: 0x64710000

### OS profile
- Current: `ipados-17.7.11-21H461` (iPadOS 17.7.11, arm64) — closest available.
- Target: iOS 16.7.16 (iPhone X, D22AP, 20H392) — no UniXNU profile exists yet.
  Reference: `github.com/ampekk/UniXNU-hotdog` (iPhone X iOS 16.7.16 on OnePlus 7T Pro).
  IPSW: `iPhone10,3,iPhone10,6_16.7.16_20H392_Restore.ipsw`.
- iPadOS userland will boot (shared arm64 frameworks) but UI is tablet-layout.
- SIM/cellular needs a Unisoc baseband driver (not yet written).

### Reference repositories
- `../unixnu-eebbk-a2_x2-ums512` — UMS512/T610, same Unisoc family, working UEFI + UniXNU
- `../unixnu-core` — UniXNU core (profiles, package/UniXNUPkg, drivers/DarwinBoot)
- `../mu_plus` — MsCorePkg/MsGraphicsPkg/PcBdsPkg (EDK2 dependencies)
- `../mu_oem_sample` — OemPkg (EDK2 dependency)

### Scripts
- `scripts/assemble_bootshim_fd.py` — compiles BootShim.S, appends UEFI FD
- `scripts/pack_unixnu_boot.py` — packs boot.img Android v2 (preserves header from boot_b)
- `scripts/avb_sign.py` — AVB SHA256_RSA4096 signing (rollback index 2)
- `scripts/flash_boot_a.py` — root + dd to boot_a + hash verify + slot switch
- `scripts/boot_unixnu.py` — slot switch + boot monitor automation
