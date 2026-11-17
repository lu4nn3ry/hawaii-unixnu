#!/usr/bin/env python3
"""Android boot image writer for hawaii (Moto E32 / UMS9230).

Follows the Mu-Silicium mkbootimg.py pattern used by device ports.
Writes an Android boot image header v2 with the configured offsets,
gzips BootShim + FD, appends the DTB.
"""
import argparse
import gzip
import struct
import sys

ANDROID_MAGIC = b"ANDROID!"
BOOT_MAGIC_SIZE = 8
BOOT_EXTRA_MAGIC_SIZE = 16


def u32_le(val):
    return struct.pack("<I", val)


def main():
    parser = argparse.ArgumentParser(description="Build hawaii Android boot image")
    parser.add_argument("--kernel", required=True, help="BootShim + FD binary (gzipped)")
    parser.add_argument("--ramdisk", required=True, help="RAM disk image")
    parser.add_argument("--dtb", required=True, help="Device tree binary")
    parser.add_argument("--output", required=True, help="Output boot image path")
    parser.add_argument("--base", type=lambda x: int(x, 0), default=0x0)
    parser.add_argument("--kernel-offset", type=lambda x: int(x, 0), default=0x8000)
    parser.add_argument("--ramdisk-offset", type=lambda x: int(x, 0), default=0x5400000)
    parser.add_argument("--tags-offset", type=lambda x: int(x, 0), default=0x100)
    parser.add_argument("--pagesize", type=int, default=2048)
    parser.add_argument("--header-version", type=int, default=2)
    parser.add_argument("--cmdline", default="console=ttyS1,115200n8 buildvariant=user")
    args = parser.parse_args()

    kernel_data = open(args.kernel, "rb").read()
    ramdisk_data = open(args.ramdisk, "rb").read()
    dtb_data = open(args.dtb, "rb").read()

    cmdline = (args.cmdline + "\0").encode("ascii")
    cmdline = cmdline.ljust(512, b"\0")

    # Android boot image header v2
    header = bytearray(BOOT_MAGIC_SIZE)
    header += u32_le(len(kernel_data))
    header += u32_le(len(ramdisk_data))
    header += u32_le(len(dtb_data)) if args.header_version >= 1 else b"\x00" * 4
    header += u32_le(len(cmdline))
    header += u32_le(args.base)
    header += u32_le(args.kernel_offset)
    header += u32_le(args.ramdisk_offset)
    header += u32_le(args.tags_offset)
    header += b"\x00" * 32  # board name
    header += u32_le(args.pagesize)
    header += u32_le(args.header_version)
    header += u32_le(0)  # ramdisk_size (deprecated, v1)
    header += b"\x00" * 128  # reserved

    # Header v2 extras
    if args.header_version >= 2:
        header += b"\x00" * BOOT_EXTRA_MAGIC_SIZE  # recovery DTBO size/offset
        header += u32_le(len(dtb_data))  # dtb_size

    image = bytearray(header)
    image += cmdline
    image += kernel_data
    image += ramdisk_data
    image += dtb_data

    # Pad to page size
    page_mask = args.pagesize - 1
    pad = (-len(image)) & page_mask
    image += b"\x00" * pad

    with open(args.output, "wb") as f:
        f.write(image)

    print(f"boot image written: {args.output} ({len(image)} bytes)")


if __name__ == "__main__":
    main()
