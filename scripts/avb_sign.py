#!/usr/bin/env python3
"""
Assinatura AVB (Android Verified Boot) para boot.img do UniXNU.

Implementa SHA256_RSA4096 com rollback index 2, conforme usado pelo
projeto motorola-moto-e32-root.

Formato da imagem assinada:
  [Imagem boot][vbmeta AVB0][padding][AVBf footer]

O AVBf footer (64 bytes no final da partição) contém:
  - Magic: 'AVBf'
  - Versão do algoritmo
  - Tamanho da imagem assinada
  - Offset do vbmeta
  - Tamanho do vbmeta
  - Hash SHA-256 da imagem
  - Assinatura RSA-4096 do hash
  - Salt
  - Rollback index
  - Flags
"""

import argparse
import hashlib
import json
import os
import struct
import sys
from pathlib import Path

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

PARTITION_SIZE = 67108864  # 64 MiB
AVB_MAGIC = b'AVB0'
AVBF_MAGIC = b'AVBf'
AVBf_FOOTER_SIZE = 64
ALGORITHM = "SHA256_RSA4096"
ROLLBACK_INDEX = 2
SALT = bytes.fromhex("f83b993601311bca149a573c1e737666ff011f6cf2aa2a5ae822f91b97af0991")


def generate_rsa_key(key_path):
    """Gera uma chave RSA-4096 para assinatura AVB."""
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
        backend=default_backend()
    )
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    Path(key_path).write_bytes(pem)
    print(f"Chave RSA-4096 gerada: {key_path}")
    return key


def load_rsa_key(key_path):
    """Carrega uma chave RSA-4096 existente."""
    pem = Path(key_path).read_bytes()
    key = serialization.load_pem_private_key(
        pem,
        password=None,
        backend=default_backend()
    )
    return key


def avb_sign_image(image_path, key_path, output_path, salt=SALT,
                   rollback_index=ROLLBACK_INDEX):
    """Assina uma imagem boot com AVB SHA256_RSA4096."""

    if not CRYPTO_AVAILABLE:
        print("ERRO: Biblioteca 'cryptography' não disponível.")
        print("Instale com: pip install cryptography")
        sys.exit(1)

    image = Path(image_path).read_bytes()
    image_size = len(image)

    print(f"Imagem: {image_path} ({image_size} bytes)")

    # Carregar ou gerar chave
    if not Path(key_path).exists():
        print(f"Chave não encontrada: {key_path}")
        print("Gerando nova chave RSA-4096...")
        key = generate_rsa_key(key_path)
    else:
        print(f"Usando chave: {key_path}")
        key = load_rsa_key(key_path)

    # Calcular SHA-256 da imagem
    digest = hashlib.sha256(image).digest()
    print(f"SHA-256 da imagem: {digest.hex()}")

    # Assinar com RSA-4096 + PKCS1v15 + SHA-256
    signature = key.sign(
        digest,
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    print(f"Assinatura RSA-4096: {len(signature)} bytes")

    # Construir vbmeta AVB0
    # Estrutura simplificada do vbmeta para add_hash_footer
    vbmeta = bytearray()

    # Magic
    vbmeta += AVB_MAGIC  # 4 bytes

    # Versão do algoritmo (0 = SHA256_RSA4096)
    vbmeta += struct.pack("<I", 0)  # 4 bytes

    # Tamanho do vbmeta (será preenchido depois)
    vbmeta_size_offset = len(vbmeta)
    vbmeta += struct.pack("<I", 0)  # 4 bytes

    # Tamanho da imagem assinada
    vbmeta += struct.pack("<Q", image_size)  # 8 bytes

    # Offset da imagem no vbmeta (0 = imagem está separada)
    vbmeta += struct.pack("<Q", 0)  # 8 bytes

    # Tamanho da imagem no vbmeta
    vbmeta += struct.pack("<Q", image_size)  # 8 bytes

    # Hash SHA-256
    vbmeta += digest  # 32 bytes

    # Assinatura
    vbmeta += signature  # 512 bytes (RSA-4096)

    # Salt
    vbmeta += salt  # 32 bytes

    # Rollback index
    vbmeta += struct.pack("<Q", rollback_index)  # 8 bytes

    # Flags
    vbmeta += struct.pack("<I", 0)  # 4 bytes

    # Preencher vbmeta para múltiplo de 4096 (alinhamento)
    vbmeta_size = len(vbmeta)
    vbmeta_pad = (-vbmeta_size) % 4096
    vbmeta += b"\x00" * vbmeta_pad
    vbmeta_size = len(vbmeta)

    # Atualizar tamanho do vbmeta
    struct.pack_into("<I", vbmeta, vbmeta_size_offset, vbmeta_size)

    print(f"vbmeta AVB0: {vbmeta_size} bytes")

    # Montar imagem final:
    # [imagem boot][vbmeta AVB0][padding até 64 MiB][AVBf footer]

    # Calcular espaço para vbmeta + footer
    vbmeta_with_pad = vbmeta_size
    footer_offset = PARTITION_SIZE - AVBf_FOOTER_SIZE

    # A imagem deve caber antes do vbmeta + footer
    max_image_size = footer_offset - vbmeta_with_pad
    if image_size > max_image_size:
        print(f"ERRO: Imagem ({image_size} bytes) muito grande para {max_image_size} bytes disponíveis")
        sys.exit(1)

    # Construir imagem final
    final = bytearray(PARTITION_SIZE)

    # Copiar imagem no início
    final[0:image_size] = image

    # Colocar vbmeta após a imagem (alinhado a 4096)
    vbmeta_offset = ((image_size + 4095) // 4096) * 4096
    final[vbmeta_offset:vbmeta_offset + vbmeta_size] = vbmeta

    # Construir AVBf footer (64 bytes no final da partição)
    footer = bytearray(AVBf_FOOTER_SIZE)

    # Magic
    footer[0:4] = AVBF_MAGIC

    # Versão do algoritmo (0 = SHA256_RSA4096)
    struct.pack_into("<I", footer, 4, 0)

    # Tamanho da imagem assinada (incluindo vbmeta?)
    struct.pack_into("<Q", footer, 8, image_size)

    # Offset do vbmeta
    struct.pack_into("<Q", footer, 16, vbmeta_offset)

    # Tamanho do vbmeta
    struct.pack_into("<Q", footer, 24, vbmeta_size)

    # Hash SHA-256 da imagem (primeiros 32 bytes)
    footer[32:64] = digest

    # Colocar footer no final da partição
    final[footer_offset:footer_offset + AVBf_FOOTER_SIZE] = footer

    # Salvar
    Path(output_path).write_bytes(bytes(final))
    print(f"\nImagem assinada: {output_path} ({len(final)} bytes)")
    print(f"  vbmeta offset: 0x{vbmeta_offset:x} ({vbmeta_offset} bytes)")
    print(f"  vbmeta size: {vbmeta_size} bytes")
    print(f"  AVBf footer offset: 0x{footer_offset:x}")
    print(f"  SHA-256: {digest.hex()}")
    print(f"  Rollback index: {rollback_index}")


def main():
    ap = argparse.ArgumentParser(description="Assinar boot.img com AVB SHA256_RSA4096")
    ap.add_argument("image", help="Imagem boot não-assinada")
    ap.add_argument("--key", default="artifacts/kernel-build/avb-test-key.pem",
                    help="Chave RSA privada (padrão: artifacts/kernel-build/avb-test-key.pem)")
    ap.add_argument("--output", required=True, help="Arquivo de saída assinado")
    ap.add_argument("--salt", default=None,
                    help="Salt em hex (padrão: salt do projeto E32)")
    ap.add_argument("--rollback-index", type=int, default=ROLLBACK_INDEX,
                    help="Rollback index (padrão: 2)")
    args = ap.parse_args()

    salt = SALT
    if args.salt:
        salt = bytes.fromhex(args.salt)

    avb_sign_image(args.image, args.key, args.output, salt, args.rollback_index)


if __name__ == "__main__":
    main()
