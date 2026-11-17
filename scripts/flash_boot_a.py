#!/usr/bin/env python3
"""Flash the UniXNU boot.img to boot_a via root dd, then set slot a and reboot.

Requires:
  - Device booted to Android (adb device online)
  - mali_kroot in /data/local/tmp/ (CVE-2021-28663 root exploit)

Run:  python scripts/flash_boot_a.py
"""

import hashlib
import os
import subprocess
import sys
import time

ADB = os.environ.get(
    "ADB",
    r"C:\Users\luann\AppData\Local\Android\Sdk\platform-tools\adb.exe",
)
IMAGE = "out/hawaii/boot/boot_unixnu_signed.img"


def run(cmd, timeout=120):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except FileNotFoundError:
        return 127, "", "not found: " + cmd[0]


def adb(*args, timeout=120):
    return run([ADB, *args], timeout=timeout)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1 << 20)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def main():
    # Check device
    rc, out, _ = adb("devices")
    if "\tdevice" not in out:
        print("[-] No adb device. Connect phone and enable USB debugging.")
        return 1
    print("[+] adb device online")

    # Check root
    rc, out, _ = adb("shell", "su", "-c", "id", "-u")
    print("    su -c id -u:", out)
    if out.strip() != "0":
        print("[*] Not root. Running mali_kroot exploit...")
        rc, out, _ = adb("shell", "su", "-c", "ls /data/local/tmp/mali_kroot")
        if "No such file" in out:
            print("[-] mali_kroot not found in /data/local/tmp/")
            print("    Push it first: adb push artifacts/mali_kroot /data/local/tmp/")
            return 1
        print("[*] Running mali_kroot...")
        rc, out, _ = adb("shell", "su", "-c", "/data/local/tmp/mali_kroot", timeout=60)
        print(out[-500:] if len(out) > 500 else out)
        # Verify root
        rc, out, _ = adb("shell", "id", "-u")
        print("    id -u after exploit:", out)
        if out.strip() != "0":
            print("[-] Root exploit failed.")
            return 1

    # Push image
    img_size = os.path.getsize(IMAGE)
    host_hash = sha256_file(IMAGE)
    print(f"\n[*] Pushing {IMAGE} ({img_size} bytes, sha256={host_hash[:16]}...)")
    rc, out, _ = adb("push", IMAGE, "/data/local/tmp/boot_unixnu.img")
    if rc != 0:
        print(f"[-] Push failed: {out}")
        return 1
    print("[+] Image pushed")

    # DD to boot_a
    print("[*] Flashing boot_a via dd...")
    rc, out, _ = adb(
        "shell", "su", "-c",
        "cat /data/local/tmp/boot_unixnu.img > /dev/block/by-name/boot_a",
        timeout=120,
    )
    if rc != 0:
        print(f"[-] dd write failed: {out}")
        return 1
    print("[+] boot_a written")

    # Verify
    print("[*] Verifying read-back...")
    rc, out, _ = adb(
        "shell", "su", "-c",
        "sha256sum /dev/block/by-name/boot_a",
        timeout=120,
    )
    dev_hash = out.split()[0] if out else ""
    print(f"    device sha256: {dev_hash}")
    print(f"    host sha256:   {host_hash}")
    if dev_hash != host_hash:
        print("[-] HASH MISMATCH!")
        return 1
    print("[+] VERIFY OK - hashes match")

    # Set slot a
    print("\n[*] Rebooting to fastboot to set slot a...")
    adb("reboot", "bootloader")
    print("    Waiting for fastboot...")
    fastboot = os.environ.get(
        "FASTBOOT",
        r"C:\Users\luann\AppData\Local\Android\Sdk\platform-tools\fastboot.exe",
    )
    for i in range(30):
        rc, out, _ = run([fastboot, "devices"], timeout=10)
        if out and "fastboot" in out.lower():
            print("[+] fastboot device online")
            break
        time.sleep(2)
    else:
        print("[-] fastboot device did not appear")
        return 1

    rc, out, _ = run([fastboot, "set_active", "a"], timeout=30)
    print(f"    set_active a: {out}")
    rc, out, _ = run([fastboot, "reboot"], timeout=30)
    print(f"    reboot: {out}")

    print("\n=== DONE ===")
    print("Device is rebooting from slot a (UniXNU).")
    print("Monitor the screen for:")
    print("  - Green bar (DarwinBoot handoff)")
    print("  - Diagnostic page with build-tag=hawaii-001")
    print("  - Panic screen if XNU fails")
    print("  - If Android boots: UniXNU failed, fell back to slot b")
    return 0


if __name__ == "__main__":
    sys.exit(main())