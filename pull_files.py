import subprocess
import os

src_dir = "/mnt/d/GitHub/hawaii-unixnu/extracted"
os.makedirs(src_dir, exist_ok=True)

files = [
    ("cmdline.txt", "cmdline.txt"),
    ("iomem.txt", "iomem.txt"),
    ("hawaii-live.dtb", "hawaii-live.dtb"),
    ("boot_b-original.img", "boot_b-original.img"),
    ("uboot_b.img", "uboot_b.img"),
]

for remote, local in files:
    local_path = os.path.join(src_dir, local)
    try:
        result = subprocess.run(
            ["cmd.exe", "/c", r"C:\Users\luann\AppData\Local\Android\Sdk\platform-tools\adb.exe", "pull", f"/data/local/tmp/{remote}", local_path],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            size = os.path.getsize(local_path) if os.path.exists(local_path) else 0
            print(f"OK: {local} ({size} bytes)")
        else:
            print(f"FALHA: {local} - {result.stderr.strip()}")
    except Exception as e:
        print(f"ERRO {local}: {e}")

print(f"\nArquivos em {src_dir}:")
for f in sorted(os.listdir(src_dir)):
    path = os.path.join(src_dir, f)
    print(f"  {f}: {os.path.getsize(path)} bytes")
