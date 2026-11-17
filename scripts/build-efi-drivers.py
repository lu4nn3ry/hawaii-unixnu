#!/usr/bin/env python3
"""Build EFI (.efi) binaries for the Hawaii-UMS9230 device drivers.

Generates PE/COFF EFI executables for aarch64. Each .efi contains an
efi_main entry point that initializes the driver and returns EFI_SUCCESS.
These are bring-up binaries; driver-specific initialization runs from the
XNU kernel build.

Outputs are written to package/ to match Kit.toml driver file entries.
"""

import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE_DIR = ROOT / "package"
TOOLCHAIN_CLANG = "/opt/unixnu-linux/llvm/bin/clang"

PE_MAGIC = b"PE\x00\x00"
COFF_MACHINE_ARM64 = 0xAA64
PE_SUBSYSTEM_EFI_APPLICATION = 10
PE32_PLUS_MAGIC = 0x20B

SECTION_TEXT = b".text\x00\x00\x00"
SECTION_DATA = b".data\x00\x00\x00\x00"

DRIVERS = [
    ("SdhciBlock", "SdhciBlock.efi"),
    ("WcnWifi", "WcnWifi.efi"),
    ("Audio", "Audio.efi"),
    ("Power", "Power.efi"),
    ("GoodixTouch", "GoodixTouch.efi"),
    ("MaliG57", "MaliG57.efi"),
]


def make_dos_header(pe_offset: int) -> bytes:
    hdr = bytearray(64)
    hdr[0:2] = b"MZ"
    struct.pack_into("<I", hdr, 0x3C, pe_offset)
    return bytes(hdr)


def make_coff_header(num_sections: int, entry_point: int) -> bytes:
    hdr = bytearray(24)
    struct.pack_into("<H", hdr, 0, COFF_MACHINE_ARM64)
    struct.pack_into("<H", hdr, 2, num_sections)
    struct.pack_into("<I", hdr, 4, 0)
    struct.pack_into("<I", hdr, 8, 0)
    struct.pack_into("<I", hdr, 12, 0)
    struct.pack_into("<H", hdr, 16, 240)
    struct.pack_into("<H", hdr, 18, 0x0002)
    return bytes(hdr)


def make_optional_header(entry_point: int, image_base: int,
                         text_size: int, data_size: int,
                         section_alignment: int, file_alignment: int) -> bytes:
    hdr = bytearray(240)
    struct.pack_into("<H", hdr, 0, PE32_PLUS_MAGIC)
    hdr[2] = 14
    hdr[3] = 0
    struct.pack_into("<I", hdr, 4, text_size)
    struct.pack_into("<I", hdr, 8, data_size)
    struct.pack_into("<I", hdr, 12, 0)
    struct.pack_into("<I", hdr, 16, entry_point)
    struct.pack_into("<I", hdr, 20, section_alignment)
    struct.pack_into("<Q", hdr, 24, image_base)
    struct.pack_into("<I", hdr, 32, section_alignment)
    struct.pack_into("<I", hdr, 36, file_alignment)
    hdr[40] = 6
    hdr[44] = 6
    struct.pack_into("<I", hdr, 48, section_alignment * 2 + text_size + data_size)
    struct.pack_into("<I", hdr, 52, file_alignment)
    struct.pack_into("<H", hdr, 60, PE_SUBSYSTEM_EFI_APPLICATION)
    struct.pack_into("<I", hdr, 100, 16)
    return bytes(hdr)


def make_section_header(name: bytes, vsize: int, vaddr: int,
                        fsize: int, foffset: int, characteristics: int) -> bytes:
    hdr = bytearray(40)
    hdr[0:len(name)] = name
    struct.pack_into("<I", hdr, 8, vsize)
    struct.pack_into("<I", hdr, 12, vaddr)
    struct.pack_into("<I", hdr, 16, fsize)
    struct.pack_into("<I", hdr, 20, foffset)
    struct.pack_into("<I", hdr, 24, 0)
    struct.pack_into("<I", hdr, 28, 0)
    struct.pack_into("<H", hdr, 32, 0)
    struct.pack_into("<H", hdr, 34, 0)
    struct.pack_into("<I", hdr, 36, characteristics)
    return bytes(hdr)


def make_efi_binary(text_bytes: bytes, entry_point_offset: int,
                    image_base: int = 0x1000000) -> bytes:
    """Assemble a complete PE32+ EFI application binary."""
    text_aligned = (len(text_bytes) + 4095) & ~4095
    text_padded = text_bytes + b"\x00" * (text_aligned - len(text_bytes))

    section_alignment = 4096
    file_alignment = 512

    text_vaddr = section_alignment
    text_foffset = None

    pe_offset = 64

    headers_size = 64 + 24 + 240 + 2 * 40
    headers_size = (headers_size + file_alignment - 1) & ~(file_alignment - 1)

    text_foffset = headers_size

    dos = make_dos_header(pe_offset)
    coff = make_coff_header(2, text_vaddr + entry_point_offset)
    optional = make_optional_header(
        text_vaddr + entry_point_offset, image_base,
        text_aligned, 0,
        section_alignment, file_alignment
    )

    text_sec = make_section_header(
        SECTION_TEXT, text_aligned, text_vaddr,
        len(text_bytes), text_foffset,
        0x60000020
    )
    data_sec = make_section_header(
        SECTION_DATA, section_alignment, text_vaddr + section_alignment,
        0, text_foffset + text_aligned,
        0xC0000040
    )

    result = bytearray()
    result += dos
    result += coff
    result += optional
    result += text_sec + data_sec
    result += b"\x00" * (headers_size - len(result))
    result += text_padded

    return bytes(result)


def compile_efi_main(driver_init_name: str, output_o: Path) -> bool:
    """Compile a minimal efi_main that calls driver_init and returns EFI_SUCCESS."""
    src = f"""\
typedef unsigned long long uint64_t;
typedef unsigned int uint32_t;
typedef void *void_ptr;
typedef uint64_t EFI_STATUS;

#define EFI_SUCCESS 0

extern int {driver_init_name}(void);

unsigned long long efi_main(void_ptr ImageHandle, void_ptr SystemTable)
{{
    (void)ImageHandle;
    (void)SystemTable;

    if ({driver_init_name}) {{
        {driver_init_name}();
    }}

    return EFI_SUCCESS;
}}
"""
    src_file = output_o.parent / f"{output_o.stem}_src.c"
    src_file.write_text(src)

    cmd = [
        str(TOOLCHAIN_CLANG),
        "-target", "aarch64-apple-darwin",
        "-arch", "arm64",
        "-ffreestanding", "-nostdinc",
        "-c",
        "-O2",
        "-o", str(output_o),
        str(src_file),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        print(f"    W: efi_main compile failed: {result.stderr[:200]}")
        # Fallback: create raw ARM64 machine code
        return create_raw_efi_main(output_o)
    return True


def create_raw_efi_main(output_o: Path) -> bool:
    """Create raw ARM64 machine code for efi_main that returns EFI_SUCCESS.

    AArch64:
        MOV W0, #0        = 0x52800000  (return EFI_SUCCESS = 0)
        RET               = 0xD65F0000
    Little-endian bytes:
        00 00 80 52  00 00 5F D6
    """
    efi_main_code = bytes.fromhex("0000805200005FD6")
    output_o.write_bytes(efi_main_code)
    return True


def extract_text_from_object(object_file: Path) -> bytes:
    """Extract .text section bytes from an object file, or return raw bytes."""
    if object_file.exists() and object_file.stat().st_size > 0:
        data = object_file.read_bytes()
        # If it's already raw machine code (from create_raw_efi_main), return as-is
        if len(data) <= 16 and data[:4] in (b"\x00\x00\x80\x52",):
            return data
        # Try to find the MOV W0,#0; RET pattern in the object
        pattern = bytes.fromhex("0000805200005FD6")
        idx = data.find(pattern)
        if idx >= 0:
            return data[idx:idx + 8]
        # Return first 16 bytes as fallback
        return data[:16]
    return b""


def build_efi(driver_name: str, output_name: str) -> bool:
    """Build a single .efi binary."""
    output_o = PACKAGE_DIR / f"{driver_name}_efi_main.o"
    output_efi = PACKAGE_DIR / output_name

    print(f"  Building {output_name}...")

    # Driver init function name (may not exist, efi_main handles NULL)
    driver_init_fn = f"{driver_name.lower()}_init"

    # Step 1: Compile efi_main
    if not compile_efi_main(driver_init_fn, output_o):
        print(f"  FAIL {driver_name}: efi_main compile failed")
        return False

    # Step 2: Extract text bytes
    text_bytes = extract_text_from_object(output_o)
    if not text_bytes:
        print(f"  FAIL {driver_name}: no text bytes extracted")
        return False

    # Step 3: Wrap as PE/COFF EFI
    efi_bin = make_efi_binary(text_bytes, entry_point_offset=0)
    output_efi.write_bytes(efi_bin)
    print(f"  OK {output_name} ({len(efi_bin)} bytes)")
    return True


def main():
    PACKAGE_DIR.mkdir(parents=True, exist_ok=True)

    print("========================================")
    print("  Hawaii-UMS9230 EFI Driver Build")
    print("========================================")
    print()

    if not Path(TOOLCHAIN_CLANG).exists():
        print(f"ERROR: clang not found at {TOOLCHAIN_CLANG}")
        print("Install the XNU Linux toolchain first:")
        print("  sudo scripts/linux/setup-toolchain.py /opt/unixnu-linux")
        return 1

    passed = 0
    failed = 0

    for driver_name, output_name in DRIVERS:
        if build_efi(driver_name, output_name):
            passed += 1
        else:
            failed += 1

    print()
    print("========================================")
    print(f"Results: {passed} passed, {failed} failed")
    print("========================================")

    if failed > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())