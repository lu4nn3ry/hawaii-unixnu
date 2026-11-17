#!/usr/bin/env python3
"""
Montar o "kernel" para o boot.img do UniXNU:
  [Cabeçalho ARM64 com magic ARMd @ 0x38]
    [BootShim código]
    [UEFI FD (SILICIUM_UEFI.fd) anexado]

Este arquivo é usado como "kernel" no pack_and_sign_boot.py, que verifica
kernel[0x38:0x3c] == b"ARMd".
"""

import pathlib
import struct
import subprocess
import sys

BASE_DIR = pathlib.Path("/mnt/d/GitHub/hawaii-unixnu")
BOOTSHIM_S = BASE_DIR / "uefi-hawaii/BootShim/BootShim.S"
BOOTSHIM_O = pathlib.Path("/tmp/bootshim.o")
BOOTSHIM_BIN = pathlib.Path("/tmp/bootshim.bin")
UEFI_FD = BASE_DIR / "uefi-hawaii/Build/hawaiiPkg/DEBUG_CLANGPDB/AARCH64/FV/SILICIUM_UEFI.fd"
OUTPUT = BASE_DIR / "payload/bootshim_fd.bin"

FD_BASE = 0x80800000
FD_SIZE = 0x400000

# Cabeçalho ARM64 para o bootloader Android v2
# Offset 0x38 deve conter b"ARMd"
ARM64_HEADER_MAGIC = b"ARMd"
ARM64_HEADER_SIZE = 0x40  # 64 bytes o suficiente para conter o magic em 0x38


def compile_bootshim():
    """Compila o BootShim.S para objeto ARM64."""
    print("Compilando BootShim...")
    clang = "aarch64-linux-gnu-gcc"
    cmd = [
        clang,
        "-c",
        "-DFD_BASE=0x80800000",
        "-DFD_SIZE=0x400000",
        "-DREQUIRES_KERNEL_HEADER=1",
        "-nostdinc",
        "-I", str(BOOTSHIM_S.parent),
        "-o", str(BOOTSHIM_O),
        str(BOOTSHIM_S),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Erro na compilação: {result.stderr}")
        sys.exit(1)
    print(f"  Objeto criado: {BOOTSHIM_O}")


def convert_to_binary():
    """Converte o objeto ELF para binário bruto."""
    print("Convertendo para binário...")
    objcopy = "aarch64-linux-gnu-objcopy"
    cmd = [
        objcopy,
        "-O", "binary",
        str(BOOTSHIM_O),
        str(BOOTSHIM_BIN),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Erro na conversão: {result.stderr}")
        sys.exit(1)
    size = BOOTSHIM_BIN.stat().st_size
    print(f"  Binário criado: {BOOTSHIM_BIN} ({size} bytes)")


def create_arm64_header(kernel_size):
    """Cria cabeçalho ARM64 mínimo com magic ARMd em 0x38."""
    hdr = bytearray(ARM64_HEADER_SIZE)
    # Preencher com zeros
    # Magic ARMd em 0x38
    hdr[0x38:0x3c] = ARM64_HEADER_MAGIC
    return bytes(hdr)


def main():
    if not BOOTSHIM_S.exists():
        print(f"ERRO: {BOOTSHIM_S} não encontrado")
        sys.exit(1)

    if not UEFI_FD.exists():
        print(f"ERRO: {UEFI_FD} não encontrado")
        sys.exit(1)

    compile_bootshim()
    convert_to_binary()

    bootshim_bin = BOOTSHIM_BIN.read_bytes()
    uefi_fd = UEFI_FD.read_bytes()

    # Verificar que o BootShim tem o magic ARMd em 0x38 (cabeçalho ARM64 válido)
    if bootshim_bin[0x38:0x3c] != ARM64_HEADER_MAGIC:
        print(f"ERRO: BootShim não tem magic ARMd em 0x38: {bootshim_bin[0x38:0x3c]}")
        sys.exit(1)

    # Montar: [BootShim (cabeçalho ARM64 + código)][UEFI FD]
    # NÃO prepender cabeçalho sintético — o BootShim já é uma imagem ARM64 válida.
    combined = bootshim_bin + uefi_fd

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(combined)

    print(f"\n=== Resultado ===")
    print(f"  BootShim: {len(bootshim_bin)} bytes")
    print(f"  UEFI FD: {len(uefi_fd)} bytes")
    print(f"  Total: {len(combined)} bytes")
    print(f"  Arquivo: {OUTPUT}")
    print(f"  ARMd magic @ 0x38: {combined[0x38:0x3c]}")
    print(f"  Entry code @ 0x00: {combined[0x00:0x04].hex()}")
    print(f"\nPróximo passo:")
    print(f"  python3 scripts/pack_unixnu_boot.py \\")
    print(f"    --base extracted/boot_b-original.img \\")
    print(f"    --bootshim {OUTPUT} \\")
    print(f"    --payload payload/payload_fat.img \\")
    print(f"    --output out/hawaii/boot/boot_unixnu.img")


if __name__ == "__main__":
    main()
