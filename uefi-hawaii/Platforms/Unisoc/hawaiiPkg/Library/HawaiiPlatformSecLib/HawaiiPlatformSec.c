/**
  Hawaii platform specific SEC hooks.

  Two stage markers while SEC is being brought up:
    - Assembly hook: paints panel CYAN (0x07FF)
    - C hook: paints panel MAGENTA (0xF81F)

  The colour on screen says how far SEC got:
    Black screen = BootShim or SEC entry faulted before assembly hook
    Cyan         = SEC assembly ran, C hook faulted
    Magenta      = SEC C ran, serial/DXE faulted
    Text         = SEC completed, DXE running

  Copyright (c) 2026. SPDX-License-Identifier: BSD-2-Clause-Patent
**/

#include <Uefi.h>
#include <Library/PlatformSecLib.h>
#include <Library/HobLib.h>
#include <Guid/EventGroup.h>

#define HAWAII_FB_BASE      0x9E000000U
#define HAWAII_FB_PIXELS    (720U * 1600U)

STATIC
VOID
HawaiiPaint (
  IN UINT32  Colour
  )
{
  volatile UINT32  *Pixel;
  UINT32           Index;

  Pixel = (volatile UINT32 *)(UINTN)HAWAII_FB_BASE;
  for (Index = 0; Index < HAWAII_FB_PIXELS; Index++) {
    Pixel[Index] = Colour;
  }
}

VOID
PlatformInitialize (
  VOID
  )
{
  UINT64  Fdt;
  EFI_GUID  EntryArgGuid = {
    0xDAEE82E6, 0x8090, 0x4E72,
    { 0xBF, 0xB9, 0x78, 0xC1, 0x3C, 0xD4, 0xE3, 0x59 }
  };

  /* Paint magenta to confirm SEC C code reached. */
  HawaiiPaint (0xFFFF00FF);   /* magenta in ARGB */

  /* Read FDT address saved by assembly hook at 0x80700000 */
  Fdt = *(volatile UINT64 *)(UINTN)0x80700000;
  if (Fdt != 0) {
    /* Create Entry-Argument HOB so UniXNURamDiskDxe can find the FDT */
    VOID  *Hob;
    Hob = BuildGuidHob (&EntryArgGuid, sizeof (UINT64));
    if (Hob != NULL) {
      *(UINT64 *)GET_GUID_HOB_DATA (Hob) = Fdt;
    }
  }
}