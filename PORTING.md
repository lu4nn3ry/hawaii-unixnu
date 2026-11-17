
## Kernel Drivers

### Building Drivers

Each driver has a corresponding build script in scripts/:

```
# Build SDHCI Block driver
python3 scripts/build-sdhci-block.py

# Build Wi-Fi driver
python3 scripts/build-wcnwifi.py

# Build Audio driver
python3 scripts/build-audio.py

# Build Power driver
python3 scripts/build-power.py

# Build GoodixTouch driver
python3 scripts/build-goodixtouch.py

# Build Mali-G57 driver
python3 scripts/build-malig57.py
```

### Driver Components

| Driver | File | Compatible | Address |
|--------|------|------------|---------|
| SdhciBlock | drivers/SdhciBlock/NativeSdhciBlock.cpp | unixnu,sdhci-block | 0x201a0000 |
| WcnWifi | drivers/WcnWifi/NativeWcnWifi.cpp | sprd,sc2355-wifi | — |
| Audio | drivers/Audio/NativeAudio.cpp | sprd,vbc-v4-codec-sc2730 | 0x1000 |
| Power | drivers/Power/NativePower.cpp | sprd,sc2731-regulator | 0x1800 |
| GoodixTouch | drivers/GoodixTouch/NativeGoodixTouch.cpp | sprd,ums9230-spi3-tp | — |
| MaliG57 | drivers/MaliG57/NativeMaliG57.cpp | sprd,mali-natt | 0x23100000 |

### Driver Development Guidelines

1. All drivers must inherit from IOService
2. Implement probe(), start(), and stop() methods
3. Use unixnu,adt-name for ADT naming
4. Use register addresses from vendor DTB
5. All drivers must be disabled by default (status = "disabled")

---

## Boot Image Packaging

### Extracting Boot Image Header

```
# Extract boot_b partition (requires root)
adb shell dd if=/dev/block/by-name/boot_b of=/tmp/boot_b.img

# Parse boot image header
python3 scripts/package.sh --extract /tmp/boot_b.img

# Or manually parse header
xxd /tmp/boot_b.img | head -4
```

### board.toml Configuration

Update board.toml with the correct boot image parameters:

```
[bootimg.image]
base = 0
kernel_offset = 0x8000
ramdisk_offset = 0x5400000
tags_offset = 0x100
pagesize = 2048
header_version = 2
```

### Creating Boot Image

```
# Package boot image
./scripts/package.sh --bootimg dts/hawaii_compiled.dtb

# Output: boot.img
```

---