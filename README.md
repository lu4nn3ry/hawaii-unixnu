# UniXNU device port: Moto E32 (hawaii / XT2227-1, Unisoc T606/UMS9230)

Community port to run iOS / iPadOS via [UniXNU](https://github.com/UniXNU/UniXNU)
on the Motorola Moto E32 (codename `hawaii`, Unisoc UMS9230 / Tiger T606).

This is a **bring-up skeleton**, not a working port. No hardware result yet.
It follows the [UniXNU device repository format](https://unixnu.com/porting/device-repository)
and the eight [porting steps](https://unixnu.com/porting/steps).

## Device facts

| Item | Value | Source |
|------|-------|--------|
| Board / codename | `hawaii` | `ro.product.board` |
| Marketing model | Motorola Moto E32 (XT2227-1) | device label |
| SoC | Unisoc UMS9230 / Tiger T606 (`qogirl6`) | `ro.board.platform=ums9230` |
| CPU | 2× Cortex-A75 + 6× Cortex-A55 @ 1,6 GHz | vendor kernel / Nura wiki |
| GPU | Mali-G57 (Valhall, JM-based, DDK r28p0) | `docs/00-device-profile.md` |
| Kernel | Linux 4.14.199+-ab612c2 | `uname -r` on device |
| Android | 11, VNDK 30, Treble enabled | `ro.vndk.version=30` |
| Boot image | Android header v2, pagesize 2048, DTB inside boot | parsed from `boot_b` |
| Bootloader | unlocked (`flash.locked=0`) | `docs/07` |
| Flash method | `dd` to `boot_b` + one-attempt slot arming | `docs/12`, `docs/16` |
| UART | `ttyS1` @ 115200n8 | vendor cmdline |
| Display | 720×1600 MIPI DSI | panel |

## Repository layout

| Path | Purpose |
|------|---------|
| `AGENTS.md` | responsibilities and required reading |
| `README.md` | board scope, prerequisites, build commands |
| `.gitignore` | local override file and generated output directories |
| `board.toml` | format 2 board configuration (name, SoC, OS profile, DTS, firmware) |
| `porting.toml` | per-area status, inputs, findings, limits, next actions |
| `feeds.toml` | SoC source feed (local `soc/UniXNU-ums9230-common` until published) |
| `local.toml.example` | local overrides template |
| `configs/hawaii_defconfig` | XNU kernel configuration |
| `dts/hawaii.dts` | board device tree (vendor DTB derived) |
| `patches/xnu/series` | ordered XNU patch series (arch → soc → device) |
| `scripts/package.sh` | device packaging script |
| `proprietary-files.txt` | required firmware files, sources and hashes |
| `package/` | device package → `kits/hawaii` in the build tree |
| `unixnu.lock` | pinned source revisions (written by `./unixnu fetch`) |

## Status

| Area | Status |
|------|--------|
| configuration | skeleton (this repo) |
| firmware | not started (no UEFI for UMS9230) |
| cpu | skeleton (DTS only) |
| memory | skeleton (reserved-memory from vendor DTB) |
| storage | not started |
| display | not started |
| gpu | not started (Mali-G57, no UniXNU component exists) |
| network | not started |
| audio | not started |
| power | not started |
| packaging | skeleton (header v2 parameters) |
| diagnostics | skeleton (UART + ramoops) |

## Build

Requires a UniXNU core checkout. This device repo is meant to be consumed via
`feeds.toml` (`kind = "soc"` pointing at `soc/UniXNU-ums9230-common`) and the
standard UniXNU build flow:

```bash
# From the UniXNU core checkout
DEVICE_DIR=../hawaii-unixnu
DEFCONFIG=hawaii_defconfig
./unixnu defconfig "$DEFCONFIG" -D "$DEVICE_DIR"
./unixnu fetch -D "$DEVICE_DIR"
./unixnu status --json -D "$DEVICE_DIR"
./unixnu tree -D "$DEVICE_DIR"
python3 scripts/porting-record.py check --device "$DEVICE_DIR"
```

## License

BSD-2-Clause-Patent (same as UniXNU core). Board-specific files keep their
own headers where copied from vendor sources.
