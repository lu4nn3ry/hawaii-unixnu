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
#define HAWAII_FB_PIXELS    (1600U * 720U)

#define HAWAII_UART1_BASE   0x200B0000U
#define HAWAII_UART_TXD     0x00U
#define HAWAII_UART_LSR     0x08U
#define HAWAII_UART_LSR_TX_OVER  (1U << 15)

STATIC
VOID
HawaiiPaint (
  IN UINT16  Colour
  )
{
  volatile UINT16  *Pixel;
  UINT32           Index;

  Pixel = (volatile UINT16 *)(UINTN)HAWAII_FB_BASE;
  for (Index = 0; Index < HAWAII_FB_PIXELS; Index++) {
    Pixel[Index] = Colour;
  }
}

STATIC
VOID
HawaiiPutc (
  IN CHAR8  Char
  )
{
  volatile UINT32  *Uart;
  UINT32           Timeout;

  Uart    = (volatile UINT32 *)(UINTN)HAWAII_UART1_BASE;
  Timeout = 256000;
  while ((Timeout-- != 0) && ((Uart[HAWAII_UART_LSR / 4] & HAWAII_UART_LSR_TX_OVER) == 0)) {
  }

  *(volatile UINT8 *)(UINTN)(HAWAII_UART1_BASE + HAWAII_UART_TXD) = (UINT8)Char;
}

VOID
PlatformInitialize (
  VOID
  )
{
  STATIC CONST CHAR8  Banner[] = "hawaiiSEC: platform C code reached\r\n";
  UINTN               Index;

  HawaiiPaint (0xF81F);   /* magenta */
  for (Index = 0; Banner[Index] != 0; Index++) {
    HawaiiPutc (Banner[Index]);
  }

  /* No hold, no PSCI reset - let SecMain continue to DXE.
   * HawaiiBringupDxe will reset at EndOfDxe. */
}