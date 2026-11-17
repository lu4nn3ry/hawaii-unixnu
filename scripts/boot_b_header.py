#!/usr/bin/env python3
"""
boot_b_header.py — Parse Android boot image header v2 from hawaii boot_b.

Usage:
    python3 scripts/boot_b_header.py [--input dts/boot_b] [--output board_bootimg.toml]

Parses the Android boot image header (version 2) and extracts:
    - header_version, page_size, kernel_size, ramdisk_size
    - kernel_addr, ramdisk_addr, tags_offset
    - cmdline, name, extra fields
    - recovery_dtbo_size, recovery_dtbo_offset
    - header_size

Results can be used to fill board.toml [bootimg] section.

Reference: Android boot image format documentation
https://source.android.com/docs/core/ota/boot_image_format
"""

import argparse
import struct
import sys
from pathlib import Path

ANDROID_MAGIC = b"ANDROID!"

BOOTIMG_HEADER_V1_SIZE = 2048
BOOTIMG_HEADER_V2_SIZE = 2048  # v2 adds vendor fields but same base size

def parse_boot_header(data: bytes) -> dict:
    """Parse Android boot image header v1/v2."""
    if len(data) < BOOTIMG_HEADER_V1_SIZE:
        raise ValueError(f"File too small: {len(data)} bytes, need at least {BOOTIMG_HEADER_V1_SIZE}")

    magic = data[:8]
    if magic != ANDROID_MAGIC:
        raise ValueError(f"Invalid Android magic: {magic!r}, expected {ANDROID_MAGIC!r}")

    # Header v1 fields (little-endian)
    kernel_size, = struct.unpack_from("<I", data, 8)
    kernel_addr, = struct.unpack_from("<I", data, 12)
    ramdisk_size, = struct.unpack_from("<I", data, 16)
    ramdisk_addr, = struct.unpack_from("<I", data, 20)
    second_size, = struct.unpack_from("<I", data, 24)
    second_addr, = struct.unpack_from("<I", data, 28)
    tags_addr, = struct.unpack_from("<I", data, 32)
    page_size, = struct.unpack_from("<I", data, 36)
    dt_size, = struct.unpack_from("<I", data, 40)
    dt_addr, = struct.unpack_from("<I", data, 44)
    header_version, = struct.unpack_from("<I", data, 48)

    result = {
        "magic": magic.decode("ascii"),
        "kernel_size": kernel_size,
        "kernel_addr": hex(kernel_addr),
        "ramdisk_size": ramdisk_size,
        "ramdisk_addr": hex(ramdisk_addr),
        "second_size": second_size,
        "second_addr": hex(second_addr),
        "tags_addr": hex(tags_addr),
        "page_size": page_size,
        "dt_size": dt_size,
        "dt_addr": hex(dt_addr),
        "header_version": header_version,
    }

    # cmdline (512 bytes at offset 80)
    cmdline_raw = data[80:592]
    cmdline = cmdline_raw.split(b"\x00")[0].decode("utf-8", errors="replace")
    result["cmdline"] = cmdline

    # name (16 bytes at offset 592)
    name_raw = data[592:608]
    result["name"] = name_raw.split(b"\x00")[0].decode("utf-8", errors="replace")

    if header_version >= 2:
        # Header v2 fields
        recovery_dtbo_size, = struct.unpack_from("<I", data, 608)
        recovery_dtbo_offset, = struct.unpack_from("<I", data, 612)
        header_size, = struct.unpack_from("<I", data, 616)

        result.update({
            "recovery_dtbo_size": recovery_dtbo_size,
            "recovery_dtbo_offset": hex(recovery_dtbo_offset),
            "header_size": header_size,
        })

        # vendor cmdline (1024 bytes at offset 1024 in v2? Actually offset varies)
        # v2 header extends to 2048 bytes typically

    return result

def format_for_board_toml(info: dict) -> str:
    """Format parsed info as TOML for board.toml [bootimg] section."""
    lines = []
    lines.append("[bootimg]")
    lines.append(f'# Parsed from Android boot image header v{info["header_version"]}')
    lines.append(f'# Magic: {info["magic"]}')
    lines.append(f"header_version = {info['header_version']}")
    lines.append(f"pagesize = {info['page_size']}")
    lines.append(f"kernel_addr = {info['kernel_addr']}")
    lines.append(f"ramdisk_addr = {info['ramdisk_addr']}")
    lines.append(f"tags_offset = {info['tags_addr']}")
    lines.append(f'cmdline = "{info["cmdline"]}"')
    lines.append(f'# name = "{info["name"]}"')
    if "recovery_dtbo_size" in info:
        lines.append(f"# recovery_dtbo_size = {info['recovery_dtbo_size']}")
        lines.append(f"# recovery_dtbo_offset = {info['recovery_dtbo_offset']}")
        lines.append(f"# header_size = {info['header_size']}")
    lines.append("")
    lines.append("# NOTE: These values must be verified against the actual hawaii boot_b")
    lines.append("# before trusting. Values inferred from UMS512/T610 family may differ.")
    return "\n".join(lines)

def main() -> int:
    parser = argparse.ArgumentParser(description="Parse Android boot image header v2 from hawaii boot_b")
    parser.add_argument("--input", default="dts/boot_b", help="Input boot_b image path")
    parser.add_argument("--output", help="Output TOML file path")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[!] Input file not found: {input_path}")
        print("    boot_b must be extracted from the device partition first.")
        return 1

    data = input_path.read_bytes()
    print(f"[+] Read {len(data)} bytes from {input_path}")

    try:
        info = parse_boot_header(data)
    except ValueError as e:
        print(f"[!] Failed to parse boot header: {e}")
        return 1

    print(f"[+] Parsed boot image header v{info['header_version']}")
    print(f"    kernel_addr: {info['kernel_addr']}")
    print(f"    ramdisk_addr: {info['ramdisk_addr']}")
    print(f"    tags_addr: {info['tags_addr']}")
    print(f"    page_size: {info['page_size']}")
    print(f"    cmdline: {info['cmdline'][:80]}...")
    if "name" in info and info["name"]:
        print(f"    name: {info['name']}")

    toml_output = format_for_board_toml(info)
    print("\n--- board.toml [bootimg] section ---")
    print(toml_output)

    if args.output:
        Path(args.output).write_text(toml_output)
        print(f"[+] Written to {args.output}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
