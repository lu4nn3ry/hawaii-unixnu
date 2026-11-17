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
  /* Paint magenta to confirm SEC C code reached.
   * No UART access here - UART1 is not clocked/powered at SEC stage.
   * Any MMIO to 0x200B0000 causes external abort -> CpuDeadLoop.
   * SerialPortWrite will write to framebuffer + ramoops only (no UART). */
  HawaiiPaint (0xFFFF00FF);   /* magenta in ARGB */
}