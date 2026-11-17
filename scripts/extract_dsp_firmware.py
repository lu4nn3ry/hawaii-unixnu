#!/usr/bin/env python3
"""
extract_audio_dsp.py - Extrair firmware DSP e ABI da partição vendor via adb

Extrai o firmware do DSP de áudio e informações de ABI para o driver de áudio
do Moto E32 (hawaii / UMS9230 / T606).

Uso:
    python3 scripts/extract_audio_dsp.py --output firmware_dsp/

Requisitos:
- adb instalado e dispositivo conectado
- Device com root (adb shell como root)
- Partição vendor acessível via /dev/block/by-name/

Partições comumente usadas para firmware DSP:
- /dev/block/by-name/dsp
- /dev/block/by-name/dsp1
- /dev/block/by-name/audio_dsp
- /dev/block/by-name/audio_dsp1
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
    parser = argparse.ArgumentParser(description="Extrair firmware DSP de áudio da partição vendor")
    parser.add_argument("--output", default="dsp_firmware/", help="Diretório de saída para firmware DSP")
    parser.add_argument("--partition", default="/dev/block/by-name/dsp", help="Partição do dispositivo com firmware DSP")
    args = parser.parse_args()

    print("=== Extraindo firmware DSP de áudio via adb ===\n")

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

    # Listar partições relacionadas a DSP
    print("\nProcurando partições de DSP...")
    stdout, stderr, rc = run_adb("ls /dev/block/by-name/ | grep -i dsp 2>/dev/null")
    if rc == 0 and stdout:
        print(f"    Partições de DSP encontradas:\n{stdout}")
    else:
        print("    Nenhuma partição dsp encontrada diretamente. Tentando outros nomes...")
        # Tentar outros nomes comuns
        for ptn in ["/dev/block/by-name/audio_dsp", "/dev/block/by-name/audio_dsp1", 
                    "/dev/block/by-name/dsp1", "/dev/block/by-name/dsp2"]:
            stdout, stderr, rc = run_adb(f"ls -l {ptn} 2>/dev/null")
            if rc == 0:
                print(f"    Encontrado: {ptn}")
                args.partition = ptn
                break
        else:
            print("[!] Nenhuma partição de DSP encontrada. Verifique manualmente.")
            return 1

    # Extrair firmware DSP
    print(f"\nExtraindo {args.partition} para /tmp/dsp_firmware.bin no dispositivo...")
    stdout, stderr, rc = run_adb(f"dd if={args.partition} of=/tmp/dsp_firmware.bin bs=4096 2>/dev/null")
    if rc != 0:
        print(f"[!] Erro ao extrair firmware DSP: {stderr}")
        return 1
    print("[+] wcnmodem.bin extraído para /tmp/wcnmodem.bin no dispositivo")

    # Copiar para o host
    print("\nCopiando firmware DSP para o host...")
    if not pull_file("/tmp/dsp_firmware.bin", args.output):
        print("[!] Falha ao copiar firmware DSP para o host")
        return 1
    print(f"[+] wcnmodem.bin copiado para {args.output}")

    # Verificar tamanho
    import os
    size = os.path.getsize(args.output)
    print(f"    Tamanho: {size} bytes")

    print("\n=== Extração concluída ===")
    print(f"Firmware DSP salvo em: {args.output}")
    print(f"Tamanho: {size} bytes")
    print("\nPróximos passos:")
    print("1. Analisar o binário do firmware DSP para extrair ABI")
    print("2. Atualizar drivers/Audio/NativeAudio.c com as informações do firmware")
    print("3. Atualizar components/Audio/Audio.toml com informações do firmware")

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
