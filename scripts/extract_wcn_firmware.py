#!/usr/bin/env python3
"""
extract_wcn_firmware.py - Extrair firmware WCN da partição vendor via adb

Extrai o arquivo wcnmodem.bin necessário para o driver Wi-Fi SC2355.

Uso:
    python3 scripts/extract_wcn_firmware.py --output wcnmodem.bin

Requisitos:
- adb instalado e dispositivo conectado
- Device com root (adb shell como root)
- Partição vendor acessível via /dev/block/by-name/wcnmodem
"""

import argparse
import subprocess
import sys
from pathlib import Path

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

def main():
    parser = argparse.ArgumentParser(description="Extrair firmware WCN via adb")
    parser.add_argument("--output", default="wcnmodem.bin", help="Arquivo de saída")
    args = parser.parse_args()

    print("=== Extraindo firmware WCN via adb ===\n")

    # Verificar se adb está disponível
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
        print("[!] Erro: dispositivo não está com root. Precisa de root para acessar partições.")
        print(f"    stdout: {stdout}")
        return 1
    print("[+] Root disponível")

    # Extrair wcnmodem.bin da partição vendor
    print("\nExtraindo /dev/block/by-name/wcnmodem para /tmp/wcnmodem.bin no dispositivo...")
    stdout, stderr, rc = run_adb("dd if=/dev/block/by-name/wcnmodem of=/tmp/wcnmodem.bin bs=4096 2>/dev/null")
    if rc != 0:
        print(f"[!] Erro ao extrair wcnmodem.bin: {stderr}")
        return 1
    print("[+] wcnmodem.bin extraído para /tmp/wcnmodem.bin no dispositivo")

    # Copiar para o host
    print("\nCopiando wcnmodem.bin para o host...")
    if not pull_file("/tmp/wcnmodem.bin", args.output):
        print("[!] Falha ao copiar wcnmodem.bin para o host")
        return 1
    print(f"[+] wcnmodem.bin copiado para {args.output}")

    # Verificar tamanho
    import os
    size = os.path.getsize(args.output)
    print(f"    Tamanho: {size} bytes")

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
