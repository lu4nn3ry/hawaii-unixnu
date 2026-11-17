# README for hawaii UEFI firmware port
#
# Follows Mu-Silicium layout:
#   https://unixnu.com/porting/uefi-firmware

This directory contains the Mu-Silicium UEFI firmware port for the
Moto E32 (hawaii / Unisoc UMS9230 / T606).

Layout:
  BootShim/          cboot trampoline (0x80080000 -> FD_BASE)
  Resources/
    Configs/hawaii.toml   [boot_shim] [uefi_fd] [boot_image_kernel] [boot_image]
    Scripts/mkbootimg.py  Android boot image writer
  Platforms/
    Unisoc/hawaiiPkg/     DSC/FDF + MemoryMapLib + UniXNU payload DXE
  Silicon/
    Unisoc/UMS9230Pkg/    SoC layer (UART, GIC, timer, DPU/GOP)

Build:
  ./unixnu build firmware --uefi ../uefi-hawaii

Status: skeleton - addresses (FD_BASE, FD_SIZE) are UNVERIFIED for
hawaii cboot. Must be measured from vendor uboot.bin before first flash.