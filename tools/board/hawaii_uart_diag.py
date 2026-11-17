#!/usr/bin/env python3
"""UART1 + ramoops diagnostic script for hawaii (Moto E32 / UMS9230).

Prepares serial console access and post-mortem log collection before first flash.
Does NOT require root. Run from host (Windows) with adb available.

Usage:
    python3 tools/board/hawaii_uart_diag.py --adb C:\\path\\to\\adb.exe [--device serial]
"""

import argparse
import subprocess
import sys
import os

ADB_DEFAULT = r"C:\\Users\\luann\\AppData\\Local\\Android\\Sdk\\platform-tools\\adb.exe"

UART1_ADDR = "0x70100000"
UART1_BAUD = 115200
RAMOOPS_ADDR = "0xfff80000"
RAMOOPS_SIZE = 0x40000  # 256 KiB
LOGOBUFFER_ADDR = "0x9e000000"
LOGOBUFFER_SIZE = 0xab0000  # ~6.7 MiB


def adb(cmd, adb_path, device=None, capture=True):
    """Run an adb command. Returns (returncode, stdout, stderr)."""
    full = [adb_path]
    if device:
        full += ["-s", device]
    full += ["shell"] + cmd
    try:
        result = subprocess.run(full, capture_output=capture, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "adb command timed out"
    except FileNotFoundError:
        return -1, "", f"adb not found at {adb_path}"


def check_uart_node(adb_path, device):
    """Verify UART1 node exists in /proc/device-tree or /sys."""
    print("== Checking UART1 device tree node ==")
    rc, out, err = adb(["ls", "/proc/device-tree/soc/"], adb_path, device)
    if rc == 0:
        print("  /proc/device-tree/soc/ contents:")
        for line in out.strip().split("\n"):
            print(f"    {line}")
        if "serial" in out or "uart" in out.lower():
            print("  OK: UART/serial node found in device tree")
        else:
            print("  WARNING: No UART/serial node visible in /proc/device-tree")
    else:
        print(f"  ERROR: Cannot read /proc/device-tree: {err.strip()}")
        print("     (expected without root -- /proc/device-tree may be restricted)")


def check_ramoops(adb_path, device):
    """Check if ramoops/pstore is available."""
    print("\n== Checking ramoops/pstore ==")
    rc, out, err = adb(["ls", "/sys/fs/pstore/"], adb_path, device)
    if rc == 0:
        print("  /sys/fs/pstore/ contents:")
        for line in out.strip().split("\n"):
            print(f"    {line}")
        print("  OK: pstore/ramoops is accessible")
    else:
        print(f"  WARNING: pstore not accessible: {err.strip()}")
        print("     ramoops console region may not be mounted")


def check_meminfo(adb_path, device):
    """Report memory status."""
    print("\n== Memory info ==")
    rc, out, err = adb(["cat", "/proc/meminfo"], adb_path, device)
    if rc == 0:
        for line in out.strip().split("\n"):
            if any(k in line for k in ("MemTotal", "MemAvailable", "MemFree", "Cached")):
                print(f"  {line}")
    else:
        print(f"  ERROR: Cannot read /proc/meminfo: {err.strip()}")


def check_cpuinfo(adb_path, device):
    """Report CPU topology."""
    print("\n== CPU info ==")
    rc, out, err = adb(["cat", "/proc/cpuinfo"], adb_path, device)
    if rc == 0:
        for line in out.strip().split("\n"):
            if any(k in line for k in ("Processor", "part", "Hardware", "cpu cores")):
                print(f"  {line}")
    else:
        print(f"  ERROR: Cannot read /proc/cpuinfo: {err.strip()}")


def main():
    parser = argparse.ArgumentParser(description="hawaii UART + ramoops diagnostics")
    parser.add_argument("--adb", default=ADB_DEFAULT, help="Path to adb executable")
    parser.add_argument("--device", default=None, help="adb device serial (for -s)")
    args = parser.parse_args()

    if not os.path.exists(args.adb):
        print(f"ERROR: adb not found at {args.adb}")
        print("   Set --adb to the correct path or install Android platform-tools.")
        sys.exit(1)

    print(f"Using adb: {args.adb}")
    if args.device:
        print(f"Target device: {args.device}")
    print()

    check_meminfo(args.adb, args.device)
    check_cpuinfo(args.adb, args.device)
    check_uart_node(args.adb, args.device)
    check_ramoops(args.adb, args.device)

    print("\n== Diagnostic summary ==")
    print("  UART1 address: " + UART1_ADDR + " @ " + str(UART1_BAUD) + " baud")
    print("  Ramoops region: " + RAMOOPS_ADDR + " (" + str(RAMOOPS_SIZE) + " bytes)")
    print("  Logobuffer: " + LOGOBUFFER_ADDR + " (" + str(LOGOBUFFER_SIZE) + " bytes)")
    print()
    print("Next steps when root is available:")
    print("  1. Re-capture vendor DTB from /dev/block/by-name/boot_b (partition A only)")
    print("  2. Decompile DTB and compare against dts/ums9230.dtsi")
    print("  3. Capture UART1 console output during boot")
    print("  4. Collect ramoops/pstore logs after any panic")


if __name__ == "__main__":
    main()
