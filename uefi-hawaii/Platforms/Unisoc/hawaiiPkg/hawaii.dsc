##
#  EDK2 platform description for Moto E32 (hawaii / UMS9230 / T606).
#
#  The device has no UEFI firmware: cboot (U-Boot) loads the boot.img
#  kernel field to 0x80080000 and jumps to it with x0 = physical address of
#  the merged device tree.  BootShim turns that into a normal EDK2
#  entry: it copies the firmware volume to PcdFdBaseAddress (0x80800000) and
#  branches to SEC, keeping x0 intact so that SEC stashes it in the
#  gSiliciumEntryArgHobGuid HOB for DtPlatformDxe.
#
#  SPDX-License-Identifier: BSD-2-Clause-Patent
##

[Defines]
  PLATFORM_NAME                  = hawaii
  PLATFORM_GUID                  = 4D2A7C31-8E5F-4B96-A1C3-7F0D2E9B6A55
  PLATFORM_VERSION               = 0.1
  DSC_SPECIFICATION              = 0x00010005
  OUTPUT_DIRECTORY               = Build/hawaiiPkg
  SUPPORTED_ARCHITECTURES        = AARCH64
  BUILD_TARGETS                  = RELEASE|DEBUG
  SKUID_IDENTIFIER               = DEFAULT
  FLASH_DEFINITION               = hawaiiPkg/hawaii.fdf
  USE_CUSTOM_DISPLAY_DRIVER      = 0

!include UMS9230Pkg/UMS9230Pkg.dsc.inc

[PcdsFixedAtBuild]
  #
  # DDR: 4 GiB at 0x80000000 (vendor DT memory node).
  #
  gArmTokenSpaceGuid.PcdSystemMemoryBase|0x80000000

  #
  # UEFI stack: inside the "UEFI Stack" region of MemoryMapLib.
  #
  gArmPlatformTokenSpaceGuid.PcdCPUCoresStackBase|0x80480000
  gArmPlatformTokenSpaceGuid.PcdCPUCorePrimaryStackSize|0x00040000

  #
  # Debug output level.
  #
  gEfiMdePkgTokenSpaceGuid.PcdDebugPrintErrorLevel|0x8007EECF

  #
  # Debug property mask 0x02 = PRINT_ERROR only during bring-up.
  #
  gEfiMdePkgTokenSpaceGuid.PcdDebugPropertyMask|0x02

  #
  # BDS looks this GUID up in the FV.  Point it at the UEFI Shell.
  #
  gEfiMdeModulePkgTokenSpaceGuid.PcdBootManagerMenuFile|{ 0x83, 0xA5, 0x04, 0x7C, 0x3E, 0x9E, 0x1C, 0x4F, 0xAD, 0x65, 0xE0, 0x52, 0x68, 0xD0, 0xB4, 0xD1 }

  #
  # BDS copies this into gST->FirmwareVendor.
  #
  gEfiMdeModulePkgTokenSpaceGuid.PcdFirmwareVendor|L"UniXNU"
  gEfiMdeModulePkgTokenSpaceGuid.PcdFirmwareRevision|0x00010000

  #
  # SMBIOS.
  #
  gSiliciumPkgTokenSpaceGuid.PcdSmbiosSystemManufacturer|"Motorola"
  gSiliciumPkgTokenSpaceGuid.PcdSmbiosSystemModel|"Moto E32"
  gSiliciumPkgTokenSpaceGuid.PcdSmbiosSystemRetailModel|"hawaii"
  gSiliciumPkgTokenSpaceGuid.PcdSmbiosSystemRetailSku|"XT2227-1"
  gSiliciumPkgTokenSpaceGuid.PcdSmbiosSystemBoardModel|"hawaii"

  #
  # Panel: 1600x720 (vendor DTS lcd_size=1600x720).
  # 32 bpp XRGB8888 assumed; framebuffer at 0x9e000000 (logobuffer).
  #
  gSiliciumPkgTokenSpaceGuid.PcdFrameBufferWidth|1600
  gSiliciumPkgTokenSpaceGuid.PcdFrameBufferHeight|720
  gSiliciumPkgTokenSpaceGuid.PcdFrameBufferColorDepth|16

[PcdsFixedAtBuild]
  #
  # Keep the emulated NV variable store at a fixed, dedicated address.
  #
  gEfiMdeModulePkgTokenSpaceGuid.PcdEmuVariableNvStoreReserved|0x81FD0000
  gEfiMdeModulePkgTokenSpaceGuid.PcdVariableStoreSize|0x00020000

[LibraryClasses]
  #
  # Platform SEC hooks: paint stage markers on the panel (cyan = assembly ran,
  # magenta = C code ran).  Overrides the SiliciumNull default.
  #
  PlatformSecLib|hawaiiPkg/Library/HawaiiPlatformSecLib/HawaiiPlatformSecLib.inf

  #
  # Board memory map: vendor reserved-memory + cboot-owned regions.
  #
  MemoryMapLib|hawaiiPkg/Library/MemoryMapLib/MemoryMapLib.inf

  #
  # UniXNU boot manager core, shared by UniXNU.efi and the DXE drivers.
  #
  UniXNULib|UniXNUPkg/Library/UniXNULib/UniXNULib.inf

  #
  # UEFI Shell libraries.
  #
  ShellLib|ShellPkg/Library/UefiShellLib/UefiShellLib.inf
  ShellCommandLib|ShellPkg/Library/UefiShellCommandLib/UefiShellCommandLib.inf
  HandleParsingLib|ShellPkg/Library/UefiHandleParsingLib/UefiHandleParsingLib.inf

[Components]
  #
  # Bring-up probe: resets to Android at EndOfDxe so every test ends with
  # a readable ramoops log instead of a black screen.
  #
  hawaiiPkg/Drivers/HawaiiBringupDxe/HawaiiBringupDxe.inf

  #
  # FV as a read-only file system, so the Shell can auto-run startup.nsh.
  #
  MdeModulePkg/Universal/FvSimpleFileSystemDxe/FvSimpleFileSystemDxe.inf

  #
  # UEFI Shell: the boot target BDS can find by FILE_GUID.
  #
  ShellPkg/Application/Shell/Shell.inf {
    <LibraryClasses>
      NULL|ShellPkg/Library/UefiShellLevel1CommandsLib/UefiShellLevel1CommandsLib.inf
      NULL|ShellPkg/Library/UefiShellLevel2CommandsLib/UefiShellLevel2CommandsLib.inf
      NULL|ShellPkg/Library/UefiShellLevel3CommandsLib/UefiShellLevel3CommandsLib.inf
    <PcdsFixedAtBuild>
      gEfiShellPkgTokenSpaceGuid.PcdShellLibAutoInitialize|FALSE
  }

  #
  # UniXNU boot manager and XNU loader (from the UniXNU core checkout).
  # UniXNUDxe registers a Boot#### option for UniXNU.efi and moves it to the
  # front of BootOrder, so BDS starts the menu automatically.
  #
  UniXNUPkg/Application/UniXNU/UniXNU.inf
  UniXNUPkg/Driver/UniXNUDxe/UniXNUDxe.inf
  UniXNUPkg/Driver/UniXNURamDiskDxe/UniXNURamDiskDxe.inf
  DarwinBootPkg/Driver/DarwinBoot.inf