#!/usr/bin/env python3
"""
Criar imagem FAT para o payload do UniXNU.

Cria um volume FAT12/FAT16 pequeno (4-8 MiB) com:
- EFI/BOOT/BOOTAA64.EFI (placeholder para o UEFI encontrar)
- unixnu.toml (configuração de inicialização do UniXNU)
"""

import argparse
import os
import pathlib
import struct
import sys

FAT12_MAX_CLUSTERS = 4084
FAT16_MAX_CLUSTERS = 65524

def create_fat_image(size_mib, label="UNIXNU  "):
    """Cria uma imagem FAT12 ou FAT16."""
    size_bytes = size_mib * 1024 * 1024

    # Determinar FAT12 ou FAT16
    total_clusters = size_bytes // 4096  # cluster de 4 KiB
    if total_clusters < FAT12_MAX_CLUSTERS:
        fat_type = 12
        fat_entries = total_clusters
        fat_size_bytes = ((fat_entries * 12 + 31) // 32) * 4  # arredondado para bytes
        fat_sectors = (fat_size_bytes + 511) // 512
    else:
        fat_type = 16
        fat_entries = total_clusters
        fat_size_bytes = fat_entries * 2
        fat_sectors = (fat_size_bytes + 511) // 512

    reserved_sectors = 1
    num_fats = 1
    root_dir_entries = 224  # para FAT12/FAT16 tradicional
    root_dir_sectors = (root_dir_entries * 32 + 511) // 512

    total_sectors = size_bytes // 512
    fat_sectors_total = fat_sectors * num_fats
    data_sectors = total_sectors - (reserved_sectors + fat_sectors_total + root_dir_sectors)
    clusters_per_cluster = 1  # 1 setor por cluster para simplificar
    data_clusters = data_sectors // clusters_per_cluster

    print(f"Criando imagem FAT{fat_type}: {size_mib} MiB")
    print(f"  Setores totais: {total_sectors}")
    print(f"  Setores reservados: {reserved_sectors}")
    print(f"  Setores FAT: {fat_sectors_total} ({num_fats} FATs de {fat_sectors} setores)")
    print(f"  Setores raiz: {root_dir_sectors}")
    print(f"  Setores de dados: {data_sectors}")
    print(f"  Clusters de dados: {data_clusters}")

    # Construir imagem
    image = bytearray(size_bytes)

    # === Boot Sector (setor 0) ===
    bs = bytearray(512)

    # Jump instruction
    bs[0:3] = b"\xEB\x3C\x90"

    # OEM Name
    bs[3:11] = b"MSDOS5.0"

    # Bytes per sector
    struct.pack_into("<H", bs, 11, 512)

    # Sectors per cluster
    bs[13] = clusters_per_cluster

    # Reserved sectors
    struct.pack_into("<H", bs, 14, reserved_sectors)

    # Number of FATs
    bs[16] = num_fats

    # Root directory entries
    struct.pack_into("<H", bs, 17, root_dir_entries)

    # Total sectors (16-bit)
    if total_sectors < 65536:
        struct.pack_into("<H", bs, 19, total_sectors)
    else:
        struct.pack_into("<H", bs, 19, 0)

    # Media descriptor
    bs[21] = 0xF8

    # Sectors per FAT
    struct.pack_into("<H", bs, 22, fat_sectors)

    # Sectors per track
    struct.pack_into("<H", bs, 24, 1)

    # Number of heads
    struct.pack_into("<H", bs, 26, 1)

    # Hidden sectors
    struct.pack_into("<I", bs, 28, 0)

    # Total sectors (32-bit)
    if total_sectors >= 65536:
        struct.pack_into("<I", bs, 32, total_sectors)

    # Drive number
    bs[36] = 0x80

    # Boot signature
    bs[38] = 0x29

    # Volume ID
    struct.pack_into("<I", bs, 39, 0x12345678)

    # Volume label (11 bytes)
    bs[43:54] = label.encode("ascii").ljust(11)

    # File system type
    bs[54:62] = b"FAT12   " if fat_type == 12 else b"FAT16   "

    # Boot code (fill with zeros)
    # ...

    # Boot signature word
    struct.pack_into("<H", bs, 510, 0xAA55)

    image[0:512] = bs

    # === FAT ===
    fat_start = reserved_sectors * 512
    for i in range(fat_sectors_total):
        fat_sector_offset = fat_start + i * 512
        if i == 0:
            # Primeira entrada do FAT (media descriptor)
            image[fat_sector_offset] = 0xF8
            image[fat_sector_offset + 1] = 0xFF
            image[fat_sector_offset + 2] = 0xFF
            if fat_type == 12:
                image[fat_sector_offset + 3] = 0xFF  # segundo byte da primeira entrada
        # O resto fica 0 (clusters livres)

    # === Root Directory ===
    root_start = (reserved_sectors + fat_sectors_total) * 512
    root_dir_offset = root_start

    # Adicionar arquivo EFI/BOOT/BOOTAA64.EFI (placeholder)
    # Na realidade, precisamos criar diretórios EFI/BOOT/
    # Por simplicidade, vamos criar apenas um arquivo na raiz

    # Criar entrada de diretório para "UNIXNU   TXT" (arquivo de configuração)
    # Entrada de diretório: 32 bytes
    # Nome (11 bytes) + Atributo (1) + Reservado (10) + Hora (2) + Data (2) +
    # Cluster inicial (2) + Tamanho (4)

    # Para simplificar, vamos criar apenas um arquivo de texto na raiz
    config_content = b"""[payload]
title = "UniXNU"
kernel = "\\EFI\\BOOT\\BOOTAA64.EFI"
timeout = 3

[kernel_args]
-v
serial=3
boot-progress=1
build-tag=hawaii-001

[payload.adt]
chip_id = "0"
owned_memory_size = "0x10000000"
root_match_volume_uuid = "REQUIRED_ROOT_VOLUME_UUID"
cpu_regs = "0,0x100"
psci_method = "smc"
packed_data_ramdisk = true
ipad_identity = true
unique_chip_id = "required"
"""

    # Criar entrada de diretório para CONFIG.TXT
    entry = bytearray(32)
    entry[0:8] = b"CONFIG   "  # nome
    entry[8:11] = b"TXT"      # extensão
    entry[11] = 0x20           # atributo: arquivo normal
    # Cluster inicial = 2 (primeiro cluster de dados)
    struct.pack_into("<H", entry, 26, 2)
    # Tamanho
    struct.pack_into("<I", entry, 28, len(config_content))

    image[root_dir_offset:root_dir_offset + 32] = entry

    # Escrever conteúdo do arquivo no primeiro cluster de dados
    data_start = (reserved_sectors + fat_sectors_total + root_dir_sectors) * 512
    image[data_start:data_start + len(config_content)] = config_content

    # Marcar cluster 2 como usado no FAT (EOF para FAT12)
    if fat_type == 12:
        # FAT12: cada entrada é 12 bits (1.5 bytes)
        # Cluster 2: bytes 3 e 4 (offset 3 do FAT)
        fat_offset = fat_start + (2 * 12) // 8  # offset no FAT
        # Para cluster 2: bits 16-27 do FAT (começando do bit 0)
        # byte 3 = bits 16-23, byte 4 = bits 24-27 + próximo
        # Valor EOF para FAT12 = 0xFFF
        image[fat_offset + 3] = 0xFF
        image[fat_offset + 4] = 0xFF  # simplificação

    return bytes(image)


def main():
    ap = argparse.ArgumentParser(description="Criar imagem FAT para payload do UniXNU")
    ap.add_argument("--size", type=int, default=8, help="Tamanho em MiB (padrão: 8)")
    ap.add_argument("--label", default="UNIXNU  ", help="Label do volume (11 chars)")
    ap.add_argument("--output", required=True, help="Arquivo de saída")
    args = ap.parse_args()

    if len(args.label) != 11:
        args.label = args.label.ljust(11)[:11]

    img = create_fat_image(args.size, args.label)

    pathlib.Path(args.output).write_bytes(img)
    print(f"\nImagem FAT escrita: {args.output} ({len(img)} bytes)")


if __name__ == "__main__":
    main()
