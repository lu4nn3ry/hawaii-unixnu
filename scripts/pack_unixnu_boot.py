#!/usr/bin/env python3
"""
Empacotador de boot.img para UniXNU no Moto E32 (UMS9230/T606)

Fluxo:
  [Cabeçalho Android v2 do boot_b original]
    [BootShim + UEFI FD]  <- "kernel" (imagem ARM64 com magic ARMd)
    [payload FAT]          <- "ramdisk" (volume FAT com unixnu.toml)
    [DTB original]
  [vbmeta AVB0 + AVBf footer]

O bootloader Android carrega o BootShim, que copia o UEFI FD para FD_BASE
e salta para ele. O UEFI então encontra o payload FAT e inicia o UniXNU.

Uso:
    python3 scripts/pack_unixnu_boot.py \
        --base extracted/boot_b-original.img \
        --bootshim uefi-hawaii/Build/hawaiiPkg/DEBUG_CLANGPDB/AARCH64/FV/SILICIUM_UEFI.fd \
        --payload payload/payload_fat.img \
        --output out/hawaii/boot/boot_unixnu.img \
        [--no-sign]
"""

import argparse
import hashlib
import pathlib
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import bootimg  # do motorola-moto-e32-root/scripts/host/

FD_BASE = 0x80800000
FD_SIZE = 0x400000  # 4 MiB
PARTITION_SIZE = 67108864  # 64 MiB
PAGE_SIZE = 2048


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def build_unixnu_boot(base_path, bootshim_fd_path, payload_path, output_path,
                      cmdline_extra=None, no_sign=False):
    """Empacota BootShim + UEFI FD + payload FAT em um boot.img Android."""

    base = pathlib.Path(base_path).read_bytes()
    h = bootimg.parse(base)
    ps = h["page_size"]

    print(f"Boot base: {base_path} ({len(base)} bytes)")
    print(f"  kernel_size: {h.get('kernel_size')}")
    print(f"  ramdisk_size: {h.get('ramdisk_size')}")
    print(f"  page_size: {ps}")
    print(f"  header_version: {h.get('header_version')}")

    # Ler BootShim + UEFI FD
    bootshim_fd = pathlib.Path(bootshim_fd_path).read_bytes()
    print(f"\nBootShim + UEFI FD: {bootshim_fd_path} ({len(bootshim_fd)} bytes)")

    # Ler payload FAT
    payload_fat = pathlib.Path(payload_path).read_bytes()
    print(f"Payload FAT: {payload_path} ({len(payload_fat)} bytes)")

    # Construir imagem
    parts = []
    hashed = []

    def emit(data):
        parts.append(data)
        pad = (-len(data)) % ps
        if pad:
            parts.append(b"\x00" * pad)

    # Kernel = BootShim + UEFI FD
    emit(bootshim_fd)
    hashed.append(bootshim_fd)

    # Ramdisk = payload FAT
    emit(payload_fat)
    hashed.append(payload_fat)

    # DTB do boot base
    dtb_size = h.get("dtb_size")
    if dtb_size:
        off = bootimg.offsets(h)["dtb"][0]
        dtb_data = base[off:off + dtb_size]
        emit(dtb_data)
        hashed.append(dtb_data)
        print(f"  DTB: {dtb_size} bytes de 0x{off:x}")

    # Cabeçalho Android v2 (cópia do base com atualizações)
    hdr = bytearray(base[:ps])

    # Atualizar kernel_size
    struct.pack_into("<I", hdr, 0x08, len(bootshim_fd))
    print(f"  kernel_size: {len(bootshim_fd)} (0x{len(bootshim_fd):x})")

    # Atualizar ramdisk_size
    struct.pack_into("<I", hdr, 0x10, len(payload_fat))
    h["ramdisk_size"] = len(payload_fat)
    print(f"  ramdisk_size: {len(payload_fat)} (0x{len(payload_fat):x})")

    # Atualizar cmdline se necessário
    if cmdline_extra:
        cur = hdr[0x40:0x40 + 512].split(b"\x00", 1)[0]
        new = (cur + b" " + cmdline_extra.encode()).ljust(512, b"\x00")
        if len(cur) + 1 + len(cmdline_extra) > 512:
            sys.exit("cmdline excederia 512 bytes")
        hdr[0x40:0x40 + 512] = new
        h["cmdline"] = new.split(b"\x00", 1)[0].decode()
        print(f"  cmdline: {h['cmdline']}")

    # Recalcular SHA-1
    digest = hashlib.sha1()
    for part in hashed:
        digest.update(part)
    hdr[0x240:0x260] = digest.digest() + bytes(12)

    img = bytes(hdr) + b"".join(parts)

    # Verificar ARMd magic
    if img[ps + 0x38:ps + 0x3c] != b"ARMd":
        # O BootShim tem o cabeçalho ARM64, mas pode não estar em ps+0x38
        # Vamos verificar se existe ARMd em qualquer lugar próximo
        found = False
        for off in range(ps, ps + 256, 4):
            if img[off:off + 4] == b"ARMd":
                print(f"  AVISO: ARMd encontrado em offset 0x{off:x}, não em 0x{ps + 0x38:x}")
                found = True
                break
        if not found:
            print(f"  AVISO: ARMd magic não encontrado no kernel empacotado")
            print(f"  Bytes em ps+0x38: {img[ps + 0x38:ps + 0x3c].hex()}")

    img_size = len(img)
    print(f"\nImagem não-assinada: {output_path} ({img_size} bytes)")
    print(f"  kernel_size: {len(bootshim_fd)} (0x{len(bootshim_fd):x})")
    print(f"  page_size: {ps}")
    print(f"  header_version: {h.get('header_version')}")
    print(f"  cmdline: {h.get('cmdline')}")

    # Verificar se cabe na partição
    if img_size > PARTITION_SIZE:
        sys.exit(f"Imagem ({img_size} bytes) excede o tamanho da partição ({PARTITION_SIZE} bytes)")

    pathlib.Path(output_path).write_bytes(img)
    print(f"\nEscrito: {output_path}")

    if not no_sign:
        print("\nAVB assinatura necessária para bootar no dispositivo.")
        print("Execute com --no-sign para gerar imagem não-assinada (para teste em QEMU).")
        print("Para assinar, use o avbtool do Android SDK.")

    return img_size


def main():
    ap = argparse.ArgumentParser(description="Empacotar boot.img do UniXNU para Moto E32")
    ap.add_argument("--base", required=True, help="boot_b original (base do cabeçalho Android)")
    ap.add_argument("--bootshim", required=True, help="BootShim + UEFI FD (SILICIUM_UEFI.fd)")
    ap.add_argument("--payload", required=True, help="Imagem FAT do payload")
    ap.add_argument("--output", required=True, help="Arquivo de saída boot.img")
    ap.add_argument("--cmdline-extra", default=None, help="Argumentos extras para o cmdline")
    ap.add_argument("--no-sign", action="store_true",
                    help="Gerar imagem não-assinada (sem AVB)")
    args = ap.parse_args()

    build_unixnu_boot(args.base, args.bootshim, args.payload, args.output,
                      args.cmdline_extra, args.no_sign)


if __name__ == "__main__":
    main()
