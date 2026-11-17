#!/usr/bin/env python3
"""Automate UniXNU boot on the Moto E32 (hawaii / UMS9230).

Flow:
  1. Wait for an adb device.
  2. Read the active slot (ro.boot.slot_suffix).
  3. If the slot is not "a", reboot to bootloader, set_active a, reboot.
  4. Monitor the slot and boot state after reboot.
     - If it stays on slot "a" and Android props appear, UniXNU boot_a
       likely failed and the bootloader fell back; report it.
     - If the slot remains "b" after the switch, set_active failed.
  5. Optionally collect ramoops/pstore once adb is back.

Run:  python scripts/boot_unixnu.py
"""

import subprocess
import sys
import time
import os

ADB = os.environ.get(
    "ADB",
    r"C:\Users\luann\AppData\Local\Android\Sdk\platform-tools\adb.exe",
)
FASTBOOT = os.environ.get(
    "FASTBOOT",
    r"C:\Users\luann\AppData\Local\Android\Sdk\platform-tools\fastboot.exe",
)


def run(cmd, timeout=30):
    """Run a command, return (returncode, stdout, stderr)."""
    try:
        p = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except FileNotFoundError:
        return 127, "", "not found: " + cmd[0]


def adb(*args, timeout=30):
    return run([ADB, *args], timeout=timeout)


def fastboot(*args, timeout=30):
    return run([FASTBOOT, *args], timeout=timeout)


def adb_getprop(prop):
    rc, out, _ = adb("shell", "getprop", prop)
    return out if rc == 0 else ""


def wait_for_adb(timeout=120):
    print("[*] Waiting for adb device...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        rc, out, _ = adb("devices")
        if "\tdevice" in out:
            print("[+] adb device online")
            return True
        time.sleep(2)
    print("[-] adb device did not appear")
    return False


def wait_for_fastboot(timeout=120):
    print("[*] Waiting for fastboot device...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        rc, out, _ = fastboot("devices")
        if out and "fastboot" in out.lower():
            print("[+] fastboot device online")
            return True
        time.sleep(2)
    print("[-] fastboot device did not appear")
    return False


def kill_stale():
    """Kill stale adb/fastboot processes that hold the USB interface."""
    print("[*] Killing stale adb/fastboot processes...")
    for name in ("adb.exe", "fastboot.exe"):
        subprocess.run(
            ["taskkill", "/F", "/IM", name],
            capture_output=True,
            text=True,
        )
    time.sleep(1)


def set_active_a():
    """Reboot to bootloader, set slot a, reboot."""
    print("[*] Rebooting to bootloader...")
    adb("reboot", "bootloader")
    if not wait_for_fastboot():
        return False

    rc, out, _ = fastboot("getvar", "current-slot")
    print("    current-slot:", out)

    print("[*] fastboot set_active a")
    rc, out, err = fastboot("set_active", "a")
    print("    set_active rc=%d out=%s err=%s" % (rc, out, err))

    rc, out, _ = fastboot("getvar", "current-slot")
    print("    current-slot after:", out)

    print("[*] fastboot reboot")
    fastboot("reboot")
    return True


def monitor(timeout=120):
    """Poll slot suffix after reboot and report boot state."""
    print("[*] Monitoring boot state for up to %ds..." % timeout)
    deadline = time.time() + timeout
    seen_android = False
    while time.time() < deadline:
        rc, out, _ = adb("devices")
        if "\tdevice" not in out:
            time.sleep(2)
            continue

        slot = adb_getprop("ro.boot.slot_suffix")
        sysname = adb_getprop("ro.build.product")
        if sysname or slot:
            seen_android = True

        print("    slot=%s build.product=%s" % (slot, sysname))

        if slot == "_a" and sysname:
            print("[!] Android is running from slot a: UniXNU boot_a did NOT take.")
            return "android_on_a"
        if slot == "_b":
            print("[!] Slot fell back to _b: UniXNU boot_a failed and bootloader reverted.")
            return "fell_back_to_b"

        time.sleep(3)

    if seen_android:
        return "android_unknown"
    print("[-] No adb response within timeout (device may be stuck or rebooting).")
    return "no_adb"


def collect_ramoops():
    """Best-effort ramoops/pstore collection once adb is back."""
    print("[*] Attempting ramoops/pstore collection...")
    rc, out, _ = adb("shell", "ls /sys/fs/pstore 2>/dev/null")
    if rc == 0 and out:
        for f in out.split():
            print("    pstore file:", f)
            adb("shell", "cat /sys/fs/pstore/%s" % f)


def main():
    kill_stale()

    if not wait_for_adb():
        print("[-] No adb device. Connect the phone via USB and retry.")
        return 1

    slot = adb_getprop("ro.boot.slot_suffix")
    print("[*] Current slot: %s" % slot)

    if slot != "_a":
        if not set_active_a():
            print("[-] Failed to set slot a.")
            return 1
    else:
        print("[*] Slot already a. Rebooting to try boot_a...")
        adb("reboot")

    result = monitor()

    # If adb is back (Android running), try to collect ramoops.
    if result in ("android_on_a", "fell_back_to_b", "android_unknown"):
        if wait_for_adb(30):
            collect_ramoops()

    print("\n=== RESULT: %s ===" % result)
    return 0


if __name__ == "__main__":
    sys.exit(main())