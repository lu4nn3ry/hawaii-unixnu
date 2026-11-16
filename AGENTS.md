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
