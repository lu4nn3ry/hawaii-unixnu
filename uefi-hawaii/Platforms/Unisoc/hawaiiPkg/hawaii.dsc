# hawaii.dsc - EDK2 DSC for Moto E32 (hawaii / UMS9230)
#
# Follows Mu-Silicium layout:
#   https://unixnu.com/porting/uefi-firmware#dsc-and-fdf
#
# REQUIRED INTEGRATION (from https://unixnu.com/porting/uefi-firmware#required-integration):
#   UniXNUPkg/Application/UniXNU/UniXNU.inf
#   UniXNUPkg/Driver/UniXNUDxe/UniXNUDxe.inf
#   DarwinBootPkg/Driver/DarwinBoot.inf
#   UniXNUPkg/Driver/UniXNURamDiskDxe/UniXNURamDiskDxe.inf
#   MdeModulePkg/Universal/Disk/DiskIoDxe/DiskIoDxe.inf
#   FatPkg/EnhancedFatDxe/Fat.inf

[Defines]
  PLATFORM_NAME           =  hawaiiPkg
  PLATFORM_GUID           =  00000000-0000-0000-0000-000000000000
  PLATFORM_VERSION        =  0.1
  PLATFORM_PACKAGE_VERSION=  0.1
  SECURITY_CLASS          =  NonEFI
  BIOS_VENDOR             =  UniXNU
  BIOS_VERSION            =  0.1
  BUILD_VERSION           =  0.1

[Packages]
  MuSiliumPkg/MuSiliumPkg.dec
  MdePkg/MdePkg.dec
  MdeModulePkg/MdeModulePkg.dec
  FatPkg/FatPkg.dec
  ShellPkg/ShellPkg.dec
  UniXNUPkg/UniXNUPkg.dec
  DarwinBootPkg/DarwinBootPkg.dec
  Silicon/Unisoc/UMS9230Pkg/UMS9230Pkg.dec

[LibraryClasses]
  HobLib|MdePkg/Library/DxeHobLib/DxeHobLib.inf
  FdtLib|MdePkg/Library/BaseFdtLib/BaseFdtLib.inf

[Components]
  ## Required by UniXNU/DarwinBoot
  UniXNUPkg/Application/UniXNU/UniXNU.inf
  UniXNUPkg/Driver/UniXNUDxe/UniXNUDxe.inf
  DarwinBootPkg/Driver/DarwinBoot.inf
  UniXNUPkg/Driver/UniXNURamDiskDxe/UniXNURamDiskDxe.inf
  MdeModulePkg/Universal/Disk/DiskIoDxe/DiskIoDxe.inf
  FatPkg/EnhancedFatDxe/Fat.inf

  ## Platform
  Platforms/Unisoc/hawaiiPkg/hawaiiPkg.inf

  ## SoC
  Silicon/Unisoc/UMS9230Pkg/UMS9230Pkg.inf

[BuildOptions]
  /* Common build flags */
  APPLICATION     _ARM_       CLANGPDB | -O2 -Wall
