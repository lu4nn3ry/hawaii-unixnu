#!/usr/bin/env python3
"""
boot_b_extract.py - Extrair boot_b header do dispositivo via adb
Extrai o cabeçalho do Android boot image da partição boot_b para preencher board.toml [bootimg]
Requisitos: adb instalado, dispositivo com root
Uso: python3 scripts/boot_b_header.py --input /dev/block/by-name/boot_b --output board_bootimg.toml
"""

import argparse
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ANDROID_MAGIC = b"ANDROID!"

def run_adb(cmd):
    """Executa comando no dispositivo via adb shell."""
    result = subprocess.run(
        ["adb", "shell", cmd],
        capture_output=True,
        text=True,
        timeout=30
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def pull_file(remote_path, local_path):
    """Copia arquivo do dispositivo para o host via adb pull."""
    result = subprocess.run(
        ["adb", "pull", remote_path, local_path],
        capture_output=True,
        text=True,
        timeout=60
    )
    return result.returncode == 0

def parse_boot_header(data):
    """Parse Android boot image header v1/v2."""
    if len(data) < 2048:
        raise ValueError(f"Arquivo muito pequeno: {len(data)} bytes, mínimo 2048")

    magic = data[:8]
    if magic != ANDROID_MAGIC:
        raise ValueError(f"Magic invalido: {magic!r}, esperado {ANDROID_MAGIC!r}")

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
        recovery_dtbo_size, = struct.unpack_from("<I", data, 608)
        recovery_dtbo_offset, = struct.unpack_from("<I", data, 612)
        header_size, = struct.unpack_from("<I", data, 616)

        result.update({
            "recovery_dtbo_size": recovery_dtbo_size,
            "recovery_dtbo_offset": hex(recovery_dtbo_offset),
            "header_size": header_size,
        })

    return result

def format_for_board_toml(info):
    """Formata informações como TOML para board.toml [bootimg]."""
    lines = []
    lines.append("[bootimg]")
    lines.append(f"# Parseado do Android boot image header v{info['header_version']}")
    lines.append(f"# Magic: {info['magic']}")
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
    lines.append("# NOTA: Estes valores devem ser verificados contra o boot_b do hawaii")
    lines.append("# antes de confiar. Valores inferidos do UMS512/T610 podem diferir.")
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Extrair cabeçalho do boot_b via adb")
    parser.add_argument("--partition", default="/dev/block/by-name/boot_b", help="Partição de boot no dispositivo")
    parser.add_argument("--output", default="board_bootimg.toml", help="Arquivo TOML de saída")
    args = parser.parse_args()

    print("=== Extraindo boot_b do dispositivo via adb ===\n")

    # Verificar se adb está disponível e dispositivo conectado
    stdout, stderr, rc = run_adb("echo 'adb_ok'")
    if rc != 0 or "adb_ok" not in stdout:
        print("[!] Erro: adb não está funcionando ou dispositivo não conectado")
        print(f"    stdout: {stdout}")
        print(f"    stderr: {stderr}")
        return 1

    print("[+] adb funcionando")

    # Verificar se temos root
    stdout, stderr, rc = run_adb("id")
    if "uid=0" not in stdout:
        print("[!] Aviso: não estamos como root. Pode ser necessário root para acessar partições.")
        print(f"    stdout: {stdout}")
    else:
        print("[+] Root disponível")

    # Extrair boot_b para /tmp no dispositivo
    print(f"\nExtraindo {args.partition} para /tmp/boot_b no dispositivo...")
    stdout, stderr, rc = run_adb(f"dd if={args.partition} of=/tmp/boot_b bs=4096 2>/dev/null")
    if rc != 0:
        print(f"[!] Erro ao extrair boot_b: {stderr}")
        return 1
    print("[+] boot_b extraído para /tmp/boot_b no dispositivo")

    # Copiar para o host
    print("\nCopiando boot_b para o host...")
    if not pull_file("/tmp/boot_b", "/tmp/hawaii_boot_b"):
        print("[!] Falha ao copiar boot_b para o host")
        return 1
    print("[+] boot_b copiado para /tmp/hawaii_boot_b")

    # Ler e analisar
    with open("/tmp/hawaii_boot_b", "rb") as f:
        data = f.read()

    print(f"\n[+] Lido {len(data)} bytes do boot_b")

    try:
        info = parse_boot_header(data)
    except ValueError as e:
        print(f"[!] Falha ao analisar cabeçalho do boot: {e}")
        return 1

    print(f"\n[+] Cabeçalho do boot image v{info['header_version']} analisado:")
    print(f"    kernel_addr: {info['kernel_addr']}")
    print(f"    ramdisk_addr: {info['ramdisk_addr']}")
    print(f"    tags_addr: {info['tags_addr']}")
    print(f"    page_size: {info['page_size']}")
    print(f"    cmdline: {info['cmdline'][:80]}...")

    toml_output = format_for_board_toml(info)
    print("\n--- board.toml [bootimg] section ---")
    print(toml_output)

    # Escrever arquivo de saída
    output_path = args.output
    with open(output_path, "w") as f:
        f.write(toml_output)
    print(f"\n[+] Escrito para {output_path}")

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
