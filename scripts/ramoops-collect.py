#!/usr/bin/env python3
"""
ramoops-collect.py — Collect pstore/ramoops console logs from hawaii (UMS9230).

Usage:
    python3 scripts/ramoops-collect.py [--device /dev/ttyUSB0] [--baud 115200] [--out pstore/]

Collects:
    - pstore/ramoops console records from /sys/fs/pstore (when booted with ramoops)
    - UART console output from hardware serial port (fallback when pstore unavailable)

Designed for the hawaii board (Moto E32 / UMS9230 / T606) where:
    - ramoops region: 0xfff80000, 256 KiB (see dts/hawaii.dts)
    - UART1: 0x200b0000, 115200n8 (see dts/hawaii.dts chosen stdout-path)
    - Root access obtained via mali_kroot (CVE-2021-28663) — adb shell as root
"""

import argparse
import os
import sys
import time
from pathlib import Path

PSTORE_DIR = Path("/sys/fs/pstore")
RAMOOPS_REGION_ADDR = 0xFFF80000
RAMOOPS_REGION_SIZE = 0x40000  # 256 KiB
UART1_ADDR = 0x200B0000
UART_BAUD = 115200


def collect_pstore(out_dir: Path) -> list:
    """Copy pstore files to out_dir."""
    out_dir.mkdir(parents=True, exist_ok=True)
    collected = []

    if not PSTORE_DIR.is_dir():
        print(f"[!] {PSTORE_DIR} not found — ramoops may not be mounted or kernel lacks pstore")
        return collected

    for entry in sorted(PSTORE_DIR.iterdir()):
        if entry.is_file():
            dest = out_dir / entry.name
            try:
                data = entry.read_bytes()
                dest.write_bytes(data)
                collected.append(dest)
                print(f"[+] Collected {entry.name} ({len(data)} bytes) -> {dest}")
            except PermissionError:
                print(f"[!] Permission denied reading {entry} — run as root")
            except OSError as e:
                print(f"[!] Error reading {entry}: {e}")

    return collected


def collect_uart(device: str, baud: int, out_dir: Path, duration_s: float = 10.0):
    """Capture UART console output for a duration."""
    try:
        import serial  # type: ignore
    except ImportError:
        print("[!] pyserial not installed — install with: pip install pyserial")
        return None

    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"uart_{int(time.time())}.log"

    try:
        with serial.Serial(device, baud, timeout=1) as ser:
            print(f"[+] Listening on {device} @ {baud} for {duration_s}s...")
            deadline = time.time() + duration_s
            with open(out_file, "wb") as f:
                while time.time() < deadline:
                    data = ser.read(4096)
                    if data:
                        f.write(data)
                        f.flush()
                        sys.stdout.write(data.decode("utf-8", errors="replace"))
                        sys.stdout.flush()
        print(f"
[+] UART capture saved to {out_file}")
        return out_file
    except serial.SerialException as e:
        print(f"[!] Serial error: {e}")
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect ramoops/pstore and UART logs from hawaii")
    parser.add_argument("--device", default="/dev/ttyUSB0", help="UART device path (default: /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, default=UART_BAUD, help="UART baud rate (default: 115200)")
    parser.add_argument("--out", default="pstore", help="Output directory (default: pstore/)")
    parser.add_argument("--uart-duration", type=float, default=10.0,
                        help="Seconds to capture UART (default: 10.0)")
    parser.add_argument("--no-uart", action="store_true", help="Skip UART capture, only pstore")
    args = parser.parse_args()

    out_dir = Path(args.out)
    print(f"=== hawaii ramoops/UART collector ===")
    print(f"  Output dir: {out_dir.resolve()}")
    print(f"  ramoops region: 0x{RAMOOPS_REGION_ADDR:08X} (+0x{RAMOOPS_REGION_SIZE:X})")
    print(f"  UART1: {args.device} @ {args.baud}")
    print()

    # Try pstore first (requires root on device + adb pull, or running on-device)
    collected = collect_pstore(out_dir)

    # UART fallback
    if not args.no_uart and not collected:
        print("[*] No pstore data found — attempting UART capture...")
        collect_uart(args.device, args.baud, out_dir, args.uart_duration)

    if not collected:
        print("[!] No data collected. Ensure device is rooted and pstore is mounted,")
        print("    or connect UART1 to host and retry with --device.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
