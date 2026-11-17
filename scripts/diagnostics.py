#!/usr/bin/env python3
"""
diagnostics.py - Script completo de diagnósticos para hawaii-unixnu
Coleta logs de ramoops, UART e informações do dispositivo para diagnóstico.
Uso: python3 scripts/diagnostics.py --output diagnostics/
"""

import argparse
import subprocess
import sys
import os
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
    parser = argparse.ArgumentParser(description="Diagnosticos do dispositivo hawaii")
    parser.add_argument("--output", default="diagnostics/", help="Diretorio de saida")
    args = parser.parse_args()

    print("=== Diagnosticos do dispositivo hawaii ===\n")

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Verificar adb
    stdout, stderr, rc = run_adb("echo 'adb_ok'")
    if rc != 0 or "adb_ok" not in stdout:
        print("[!] Erro: adb não está funcionando")
        print(f"    stdout: {stdout}")
        print(f"    stderr: {stderr}")
        return 1
    print("[+] adb funcionando")

    # Verificar root
    stdout, stderr, rc = run_adb("id")
    if "uid=0" not in stdout:
        print("[!] Aviso: dispositivo não está com root")
    else:
        print("[+] Root disponível")

    print("\n--- Coletando informações do dispositivo ===\n")

    # Comandos básicos
    commands = {
        "device_info": "uname -a",
        "root_check": "id",
        "partitions": "cat /proc/partitions",
        "mounts": "mount",
        "cpuinfo": "cat /proc/cpuinfo",
        "meminfo": "cat /proc/meminfo",
        "uptime": "uptime",
        "dmesg_tail": "dmesg | tail -50",
    }

    for name, cmd in commands.items():
        print(f"Coletando {name}...")
        stdout, stderr, rc = run_adb(cmd)
        if rc == 0:
            path = output_dir / f"{name}.txt"
            path.write_text(stdout)
            print(f"  [+] {name}: {len(stdout)} bytes")
        else:
            print(f"  [!] {name}: falhou - {stderr}")

    # Coletar ramoops
    print("\n--- Coletando ramoops/pstore ===
")
    ramoops_dir = output_dir / "ramoops"
    ramoops_dir.mkdir(exist_ok=True)

    pstore_files = ["ramoops", "console", "cpuinfo"]
    for pstore_file in pstore_files:
        remote = f"/sys/firmware/pstore/{pstore_file}"
        local = ramoops_dir / pstore_file
        stdout, stderr, rc = run_adb(f"cat {remote}")
        if rc == 0 and stdout:
            path = ramoops_dir / pstore_file
            path.write_text(stdout)
            print(f"  [+] {pstore_file}: {len(stdout)} bytes")
        else:
            print(f"  [!] {pstore_file}: não disponível ou erro: {stderr}")

    # Coletar logs de UART
    print("\n--- Coletando logs UART ===
")
    uart_dir = output_dir / "uart"
    uart_dir.mkdir(exist_ok=True)

    # Tentar ler de /dev/ttyS1 se disponível
    stdout, stderr, rc = run_adb("cat /dev/ttyS1 2>/dev/null | head -100")
    if rc == 0 and stdout:
        path = uart_dir / "uart1.txt"
        path.write_text(stdout)
        print(f"  [+] UART1 capturado: {len(stdout)} bytes")
    else:
        print("  [!] UART1 não disponível ou vazio")

    # Resumo
    print("\n=== Diagnósticos concluídos ===
")
    print(f"Diretório de saída: {output_dir.resolve()}")
    print(f"Arquivos coletados: {len(list(output_dir.rglob('*')))}")

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
