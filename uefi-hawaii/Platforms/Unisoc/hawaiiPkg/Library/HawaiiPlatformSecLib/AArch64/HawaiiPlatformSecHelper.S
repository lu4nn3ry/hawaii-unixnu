//
// Hawaii platform specific SEC assembly hook.
//
// Called from ModuleEntryPoint right after the data cache is cleaned and after
// the boot loader's x0 (the vendor FDT) has been stored in gSecEntryArg0.
//
// The panel is painted cyan. If cyan is what stays on screen, SEC entry code
// ran and the failure is after this point.
//
// Copyright (c) 2026. SPDX-License-Identifier: BSD-2-Clause-Patent
//

#include <AsmMacroLib.h>

// 0x9E000000 is the U-Boot logobuffer; panel is 720x1600 (portrait) = 1,152,000 pixels.
#define HAWAII_FB_MOVZ_HI   0x9E00
#define HAWAII_FB_PIXELS_LO 0x9400
#define HAWAII_FB_PIXELS_HI 0x0011
#define HAWAII_RGB565_CYAN  0x07FF

// Two seconds of the 26 MHz architectural counter.
#define HAWAII_HOLD_LO      0x7500
#define HAWAII_HOLD_HI      0x0319

ASM_FUNC (PlatformAssemblyInitialize)
  /* Save x0 (FDT address from bootloader) to 0x80700000 (free at SEC stage).
   * The C code (PlatformInitialize) reads it back and creates the Entry-Argument HOB. */
  movz  x3, #0x8070, lsl #16
  str     x0, [x3]

  /* 32bpp framebuffer: 720x1600 = 1,152,000 pixels * 4 bytes = 0x465000 */
  movz  x0, #HAWAII_FB_MOVZ_HI, lsl #16
  movz  w1, #0xFFFF                  /* cyan in RGB565, replicated to 32bpp */
  movk  w1, #0x07FF, lsl #16         /* 0x07FFFFFF = cyan in ARGB */
  movz  w2, #HAWAII_FB_PIXELS_LO
  movk  w2, #HAWAII_FB_PIXELS_HI, lsl #16
1:
  str     w1, [x0], #4
  subs  x2, x2, #1
  b.ne  1b

  ret