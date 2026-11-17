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

// 0x9E000000 is the U-Boot logobuffer; panel is 1600x720 = 1,152,000 = 0x119400.
#define HAWAII_FB_MOVZ_HI   0x9E00
#define HAWAII_FB_PIXELS_LO 0x9400
#define HAWAII_FB_PIXELS_HI 0x0011
#define HAWAII_RGB565_CYAN  0x07FF

// Two seconds of the 26 MHz architectural counter.
#define HAWAII_HOLD_LO      0x7500
#define HAWAII_HOLD_HI      0x0319

ASM_FUNC (PlatformAssemblyInitialize)
  movz  x0, #HAWAII_FB_MOVZ_HI, lsl #16
  movz  w1, #HAWAII_RGB565_CYAN
  movz  w2, #HAWAII_FB_PIXELS_LO
  movk  w2, #HAWAII_FB_PIXELS_HI, lsl #16
1:
  strh  w1, [x0], #2
  subs  x2, x2, #1
  b.ne  1b

  // Busy wait two seconds so a human can see the colour.
  movz  w4, #HAWAII_HOLD_LO
  movk  w4, #HAWAII_HOLD_HI, lsl #16
  mrs   x3, cntvct_el0
  add   x4, x3, x4
2:
  mrs   x3, cntvct_el0
  cmp   x3, x4
  b.lo  2b
  ret