# hawaii.dsc - EDK2 DSC for Moto E32 (hawaii / UMS9230)
#
# Follows Mu-Silicium layout:
#   https://unixnu.com/porting/uefi-firmware#dsc-and-fdf

[Defines]
  PLATFORM_NAME           =  hawaiiPkg
  PLATFORM_GUID           =  00000000-0000-0000-0000-000000000000
  PLATFORM_VERSION        =  0.1
  PLATFORM_PACKAGE_VERSION=  0.1
  SECURITY_CLASS          =  NonEFI
  BIOS_VENDOR             =  UniXNU
  BIOS_VERSION            =  0.1
  BUILD_VERSION           =  0.1
  SUPPORTED_ARCHITECTURES =  AARCH64
  BUILD_TARGETS           =  DEBUG

[Packages]
  MdePkg/MdePkg.dec
  MdeModulePkg/MdeModulePkg.dec
  FatPkg/FatPkg.dec
  ShellPkg/ShellPkg.dec

[LibraryClasses]
  HobLib|MdePkg/Library/DxeHobLib/DxeHobLib.inf
  FdtLib|MdePkg/Library/BaseFdtLib/BaseFdtLib.inf

[Components]
  ## Platform
  Platforms/Unisoc/hawaiiPkg/hawaiiPkg.inf

  ## SoC
  Silicon/Unisoc/UMS9230Pkg/UMS9230Pkg.inf

[BuildOptions]
  DEBUG_CLANGPDB_ARM64_APPLICATION_FLAGS = -O2 -Wall
  RELEASE_CLANGPDB_ARM64_APPLICATION_FLAGS = -O2 -Wall
