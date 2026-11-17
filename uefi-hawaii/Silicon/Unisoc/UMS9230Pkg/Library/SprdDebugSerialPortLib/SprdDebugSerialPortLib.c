/*
  Debug serial port for the Moto E32 (hawaii / UMS9230 / T606).

  Three sinks:
   1. UART1 at 0x200b0000 -- SoC console UART (vendor DTS serial@200b0000,
      /chosen stdout-path, kernel cmdline console=ttyS1,115200n8).
   2. ramoops console/dmesg zones at 0xfff80000.
   3. Framebuffer at 0x9e000000 (1600x720, 32bpp XRGB8888).
*/

#include <Uefi.h>
#include <Library/BaseLib.h>
#include <Library/SerialPortLib.h>

#include "SprdFont8x16.h"

#define UART1_BASE           0x200b0000ULL
#define UART_TXD             0x00
#define UART_LSR             0x08
#define UART_LSR_TX_OVER     (1U << 15)
#define UART_PROBE_TIMEOUT   20000U

#define PRZ_SIG              0x43474244U
#define PRZ_HDR              12U
#define CONSOLE_ZONE         0xFFFB0000ULL
#define CONSOLE_ZONE_DMESG   0xFFF80000ULL
#define DMESG_PREFIX         "====0.000000-0\n"
#define DMESG_PREFIX_LEN     ((UINT32)(sizeof (DMESG_PREFIX) - 1))
#define CONSOLE_CAP          (0x8000U - PRZ_HDR - DMESG_PREFIX_LEN)

STATIC UINT32   mConsolePos;
STATIC BOOLEAN  mConsoleWrapped;
STATIC BOOLEAN  mUartDead;

/* Framebuffer: 720x1600, 32bpp ARGB at 0x9e000000. */
#define FB_BASE     0x9e000000ULL
#define FB_WIDTH    720U
#define FB_HEIGHT   1600U
#define FB_BPP      4U
#define FB_STRIDE   (FB_WIDTH * FB_BPP)
#define FB_COLS     (FB_WIDTH / 8U)
#define FB_ROWS     (FB_HEIGHT / 16U)
#define FB_CELL_W   8U
#define FB_CELL_H   16U
#define FB_BG       0xFF000000U
#define FB_FG       0xFFFFFFFFU

STATIC UINT32   mFbRow;
STATIC UINT32   mFbCol;
STATIC BOOLEAN  mFbReady;

STATIC
VOID
FbFillSpan (
  IN UINT32  X,
  IN UINT32  Y,
  IN UINT32  Width,
  IN UINT32  Color
  )
{
  volatile UINT32  *Pixel;
  UINT32           Index;

  Pixel = (volatile UINT32 *)(UINTN)(FB_BASE + (UINT64)Y * FB_STRIDE + (UINT64)X * FB_BPP);

  for (Index = 0; Index < Width; Index++) {
    Pixel[Index] = Color;
  }
}

STATIC
VOID
FbClear (
  VOID
  )
{
  UINT32  Y;

  for (Y = 0; Y < FB_HEIGHT; Y++) {
    FbFillSpan (0, Y, FB_WIDTH, FB_BG);
  }
}

STATIC
VOID
FbScroll (
  VOID
  )
{
  volatile UINT32  *Dst;
  volatile UINT32  *Src;
  UINT32           Row;
  UINT32           Index;

  for (Row = FB_CELL_H; Row < FB_HEIGHT; Row++) {
    Dst = (volatile UINT32 *)(UINTN)(FB_BASE + (UINT64)(Row - FB_CELL_H) * FB_STRIDE);
    Src = (volatile UINT32 *)(UINTN)(FB_BASE + (UINT64)Row * FB_STRIDE);
    for (Index = 0; Index < FB_WIDTH; Index++) {
      Dst[Index] = Src[Index];
    }
  }

  for (Row = FB_HEIGHT - FB_CELL_H; Row < FB_HEIGHT; Row++) {
    FbFillSpan (0, Row, FB_WIDTH, FB_BG);
  }
}

STATIC
VOID
FbGlyph (
  IN UINT32  Col,
  IN UINT32  Row,
  IN UINT8   Ch,
  IN UINT32  Fg
  )
{
  CONST UINT8     *Bits;
  volatile UINT32 *Line;
  UINT32          X;
  UINT32          Y;

  if ((Col >= FB_COLS) || (Row >= FB_ROWS)) {
    return;
  }

  if ((Ch < FONT_FIRST) || (Ch > FONT_LAST)) {
    Ch = (UINT8)0x3f;
  }

  Bits = &font8x16[(Ch - FONT_FIRST) * 16];

  Line = (volatile UINT32 *)(UINTN)(FB_BASE +
                                    (UINT64)(Row * FB_CELL_H) * FB_STRIDE +
                                    (UINT64)(Col * FB_CELL_W) * FB_BPP);
  for (Y = 0; Y < FB_CELL_H; Y++) {
    for (X = 0; X < FB_CELL_W; X++) {
      if ((Bits[Y] & (UINT8)(0x80 >> X)) != 0) {
        Line[X] = Fg;
      } else {
        Line[X] = FB_BG;
      }
    }

    Line = (volatile UINT32 *)(UINTN)((UINTN)Line + FB_STRIDE);
  }
}

STATIC
VOID
FbPutc (
  IN CHAR8  C
  )
{
  UINT8  Ch;

  Ch = (UINT8)C;

  if ((Ch == 0x0a) || (Ch == 0x0d)) {
    mFbCol = 0;
    if (Ch == 0x0a) {
      mFbRow++;
    }
  } else if (Ch == 0x09) {
    mFbCol = (mFbCol + 4U) & ~3U;
  } else if ((Ch >= 0x20) && (Ch < 0x7f)) {
    FbGlyph (mFbCol, mFbRow, Ch, FB_FG);
    mFbCol++;
  } else {
    return;
  }

  if (mFbCol >= FB_COLS) {
    mFbCol = 0;
    mFbRow++;
  }

  while (mFbRow >= FB_ROWS) {
    FbScroll ();
    mFbRow--;
  }
}

STATIC
VOID
FbConWrite (
  IN UINT8  *Buffer,
  IN UINTN  NumberOfBytes
  )
{
  UINTN  Index;

  if (mFbReady == 0) {
    FbClear ();
    mFbRow   = 0;
    mFbCol   = 0;
    mFbReady = TRUE;
  }

  for (Index = 0; Index < NumberOfBytes; Index++) {
    FbPutc ((CHAR8)Buffer[Index]);
  }
}

STATIC
VOID
UartPutc (
  IN CHAR8  C
  )
{
  UINT32  Timeout;

  if (!mUartDead) {
    for (Timeout = 0; Timeout < UART_PROBE_TIMEOUT; Timeout++) {
      if ((*(volatile UINT32 *)(UINTN)(UART1_BASE + UART_LSR) & UART_LSR_TX_OVER) != 0) {
        break;
      }
    }

    if (Timeout == UART_PROBE_TIMEOUT) {
      mUartDead = TRUE;
    } else {
      *(volatile UINT32 *)(UINTN)(UART1_BASE + UART_TXD) = (UINT32)(UINT8)C;
      return;
    }
  }
}

STATIC
VOID
ConsolePublish (
  VOID
  )
{
  volatile UINT32  *Header;
  volatile UINT32  *HeaderDmesg;
  volatile UINT8   *Prefix;
  UINT32           Index;

  Header      = (volatile UINT32 *)(UINTN)CONSOLE_ZONE;
  HeaderDmesg = (volatile UINT32 *)(UINTN)CONSOLE_ZONE_DMESG;

  Prefix = (volatile UINT8 *)(UINTN)(CONSOLE_ZONE_DMESG + PRZ_HDR);
  for (Index = 0; Index < DMESG_PREFIX_LEN; Index++) {
    Prefix[Index] = (UINT8)DMESG_PREFIX[Index];
  }

  Header[0] = PRZ_SIG;
  Header[1] = mConsoleWrapped ? mConsolePos : 0;
  Header[2] = mConsoleWrapped ? CONSOLE_CAP : mConsolePos;

  HeaderDmesg[0] = PRZ_SIG;
  HeaderDmesg[1] = 0;
  HeaderDmesg[2] = DMESG_PREFIX_LEN + Header[2];
}

STATIC
VOID
ConsolePutc (
  IN CHAR8  C
  )
{
  volatile UINT8  *Data;
  volatile UINT8  *DataDmesg;

  if (mConsolePos >= CONSOLE_CAP) {
    mConsolePos      = 0;
    mConsoleWrapped  = TRUE;
  }

  Data      = (volatile UINT8 *)(UINTN)(CONSOLE_ZONE + PRZ_HDR);
  DataDmesg = (volatile UINT8 *)(UINTN)(CONSOLE_ZONE_DMESG + PRZ_HDR + DMESG_PREFIX_LEN);
  Data[mConsolePos]      = (UINT8)C;
  DataDmesg[mConsolePos] = (UINT8)C;
  mConsolePos++;
}

RETURN_STATUS
EFIAPI
SprdDebugSerialPortLibConstructor (
  VOID
  )
{
  return RETURN_SUCCESS;
}

RETURN_STATUS
EFIAPI
SerialPortInitialize (
  VOID
  )
{
  return RETURN_SUCCESS;
}

UINTN
EFIAPI
SerialPortWrite (
  IN UINT8  *Buffer,
  IN UINTN  NumberOfBytes
  )
{
  UINTN  Index;

  if (Buffer == NULL) {
    return 0;
  }

  for (Index = 0; Index < NumberOfBytes; Index++) {
    UartPutc ((CHAR8)Buffer[Index]);
    ConsolePutc ((CHAR8)Buffer[Index]);
  }

  FbConWrite (Buffer, NumberOfBytes);
  ConsolePublish ();
  return NumberOfBytes;
}

UINTN
EFIAPI
SerialPortRead (
  OUT UINT8  *Buffer,
  IN  UINTN  NumberOfBytes
  )
{
  return 0;
}

BOOLEAN
EFIAPI
SerialPortPoll (
  VOID
  )
{
  return FALSE;
}

RETURN_STATUS
EFIAPI
SerialPortSetControl (
  IN UINT32  Control
  )
{
  return RETURN_UNSUPPORTED;
}

RETURN_STATUS
EFIAPI
SerialPortGetControl (
  OUT UINT32  *Control
  )
{
  if (Control == NULL) {
    return RETURN_INVALID_PARAMETER;
  }

  *Control = 0;
  return RETURN_SUCCESS;
}

RETURN_STATUS
EFIAPI
SerialPortSetAttributes (
  IN OUT UINT64              *BaudRate,
  IN OUT UINT32              *ReceiveFifoDepth,
  IN OUT UINT32              *Timeout,
  IN OUT EFI_PARITY_TYPE     *Parity,
  IN OUT UINT8               *DataBits,
  IN OUT EFI_STOP_BITS_TYPE  *StopBits
  )
{
  return RETURN_UNSUPPORTED;
}