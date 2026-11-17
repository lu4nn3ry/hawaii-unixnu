#!/usr/bin/env python3
"""Flash UniXNU boot.img to Moto E32 (hawaii) in one shot.

Does everything:
  1. Kill stale adb/fastboot processes
  2. Set slot b (Android) if in fastboot
  3. Wait for adb
  4. Root check (su -c id -u)
  5. Push boot_unixnu_signed.img to /data/local/tmp/
  6. dd to /dev/block/by-name/boot_a
  7. Verify sha256
  8. Reboot to bootloader
  9. Set slot a
  10. Reboot

Run:  python scripts/flash_all.py
"""

import hashlib, os, subprocess, sys, time

ADB = os.environ.get("ADB", r"C:\Users\luann\AppData\Local\Android\Sdk\platform-tools\adb.exe")
FASTBOOT = os.environ.get("FASTBOOT", r"C:\Users\luann\AppData\Local\Android\Sdk\platform-tools\fastboot.exe")
IMAGE = os.path.join(os.path.dirname(__file__), "..", "out", "hawaii", "boot", "boot_unixnu_signed.img")

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

def fb(*args, timeout=30):
    return run([FASTBOOT, *args], timeout=timeout)

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1 << 20)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def kill_stale():
    print("[*] Killing stale adb/fastboot...")
    for name in ("adb.exe", "fastboot.exe"):
        subprocess.run(["taskkill", "/F", "/IM", name], capture_output=True, text=True)
    time.sleep(2)

def wait_for(tool, pattern, timeout=60):
    print(f"[*] Waiting for {tool}...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        rc, out, _ = run([tool, "devices"], timeout=10)
        if pattern in out:
            print(f"[+] {tool} online")
            return True
        time.sleep(2)
    print(f"[-] {tool} timeout")
    return False

def main():
    if not os.path.isfile(IMAGE):
        print(f"[-] Image not found: {IMAGE}")
        return 1

    img_hash = sha256_file(IMAGE)
    print(f"[*] Image: {IMAGE}")
    print(f"    Size: {os.path.getsize(IMAGE)} bytes")
    print(f"    SHA256: {img_hash}")

    kill_stale()

    # If in fastboot, set slot b and reboot to Android
    rc, out, _ = fb("devices")
    if "fastboot" in out.lower():
        print("[*] In fastboot, setting slot b...")
        fb("set_active", "b")
        fb("reboot")
        time.sleep(1)
    else:
        # Try adb
        rc, out, _ = adb("devices")
        if "\tdevice" not in out:
            print("[-] No device in adb or fastboot. Force reboot (Power 10s) and retry.")
            return 1

    # Wait for Android
    if not wait_for(ADB, "\tdevice", timeout=60):
        print("[-] Device did not boot to Android. Try: adb wait-for-device")
        return 1

    # Root check
    rc, out, _ = adb("shell", "su", "-c", "id", "-u")
    if out.strip() != "0":
        print("[-] Not root. Run mali_kroot first:")
        print("    adb push artifacts/mali_kroot /data/local/tmp/")
        print("    adb shell su -c /data/local/tmp/mali_kroot")
        return 1
    print("[+] Root OK")

    # Push
    print("[*] Pushing image...")
    rc, out, _ = adb("push", IMAGE, "/data/local/tmp/boot_unixnu.img")
    if rc != 0:
        print(f"[-] Push failed: {out}")
        return 1

    # DD
    print("[*] Flashing boot_a via dd...")
    rc, out, _ = adb("shell", "su", "-c",
        "dd if=/data/local/tmp/boot_unixnu.img of=/dev/block/by-name/boot_a bs=4M 2>&1",
        timeout=60)
    if rc != 0:
        print(f"[-] dd failed: {out}")
        return 1
    print(f"    {out}")

    # Verify
    print("[*] Verifying...")
    rc, out, _ = adb("shell", "su", "-c", "sha256sum /dev/block/by-name/boot_a", timeout=60)
    dev_hash = out.split()[0] if out else ""
    print(f"    device: {dev_hash}")
    print(f"    host:   {img_hash}")
    if dev_hash != img_hash:
        print("[-] HASH MISMATCH!")
        return 1
    print("[+] VERIFY OK")

    # Reboot to fastboot, set slot a, reboot
    print("[*] Rebooting to fastboot...")
    adb("reboot", "bootloader")
    if not wait_for(FASTBOOT, "fastboot", timeout=30):
        print("[-] fastboot timeout")
        return 1

    print("[*] Setting slot a...")
    fb("set_active", "a")

    print("[*] Rebooting to UniXNU...")
    fb("reboot")

    print("\n=== DONE ===")
    print("Device is booting UniXNU from slot a.")
    print("Watch the screen:")
    print("  GREEN/CYAN = SEC assembly ran")
    print("  MAGENTA = SEC C code ran")
    print("  TEXT = DXE running")
    print("  RESET TO ANDROID = BringupDxe fired")
    return 0

if __name__ == "__main__":
    sys.exit(main())