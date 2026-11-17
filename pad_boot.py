import shutil
import os

boot_img = "/mnt/d/GitHub/unixnu-core/out/hawaii/ipados-17.7.11-21H461/hawaii/boot/boot.img"
padded_img = "/mnt/d/GitHub/hawaii-unixnu/boot_padded.img"

size = os.path.getsize(boot_img)
block = 4096
padded_size = ((size + block - 1) // block) * block
padding = padded_size - size

print(f"Tamanho atual: {size} bytes")
print(f"Tamanho com padding: {padded_size} bytes")
print(f"Padding: {padding} bytes")

shutil.copy2(boot_img, padded_img)

with open(padded_img, "ab") as f:
    f.write(b"\x00" * padding)

print(f"Arquivo criado: {padded_img}")
print(f"Tamanho final: {os.path.getsize(padded_img)} bytes")
