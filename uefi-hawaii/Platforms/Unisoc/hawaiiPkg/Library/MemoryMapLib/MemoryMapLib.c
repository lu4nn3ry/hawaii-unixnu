/*
  Moto E32 (hawaii / UMS9230 / T606) memory map.

  Addresses from /proc/iomem on the live device:
    System RAM: 0x80000000-0x853effff (first segment ~84 MB)
    Kernel code: 0x80080000-0x813effff
    Framebuffer: 0x9e000000 (logobuffer, 1600x720 32bpp)
    Ramoops: 0xfff80000 (0x40000)
    GIC: 0x10000000
    UART1: 0x200b0000
    SDHCI: 0x201a0000
    DPU: 0x31000000
    DSI: 0x31100000
    GPIO: 0x641b0000
    EIC: 0x641000a0
    PMIC SPI: 0x64200000
    Timer: 0x64470000
    pinctrl: 0x64710000
*/

#include <Library/MemoryMapLib.h>

STATIC
EFI_MEMORY_REGION_DESCRIPTOR
gMemoryDescriptor[] = {
  // Name, Address, Length, HobOption, ResourceType, ResourceAttribute, MemoryType, ArmAttribute

  // BootShim + UEFI FD source (cboot loads here)
  {"Boot Shim",          0x80080000, 0x00400000, AddMem,  MEM_RES, UNCACHEABLE,   Reserv, UNCACHED_UNBUFFERED_XN},

  // DDR: firmware owned
  {"UEFI Stack",         0x80480000, 0x00200000, AddMem,  SYS_MEM, SYS_MEM_CAP, BsData, WRITE_BACK_XN},
  {"SEC Heap",           0x80680000, 0x00100000, AddMem,  SYS_MEM, SYS_MEM_CAP, BsData, WRITE_BACK_XN},
  {"MMU PageTables",     0x80780000, 0x00040000, AddMem,  SYS_MEM, SYS_MEM_CAP, BsData, WRITE_BACK_XN},
  {"UEFI FD",            0x80800000, 0x00400000, AddMem,  SYS_MEM, SYS_MEM_CAP, BsData, WRITE_BACK},
  {"DXE Heap",           0x80C00000, 0x013D0000, AddMem,  SYS_MEM, SYS_MEM_CAP, Conv,   WRITE_BACK_XN},
  {"VarStore",           0x81FD0000, 0x00020000, AddMem,  MEM_RES, UNCACHEABLE,   Reserv, WRITE_BACK},

  // FDT and initrd
  {"FDT",                0x82000000, 0x00100000, AddMem,  MEM_RES, UNCACHEABLE,   Reserv, WRITE_BACK_XN},
  {"Initrd",             0x82100000, 0x02000000, AddMem,  MEM_RES, UNCACHED_UNBUFFERED_XN, Reserv, UNCACHED_UNBUFFERED_XN},

  // Vendor reserved regions
  {"DDRBIST",            0x80000000, 0x00001000, AddMem,  MEM_RES, UNCACHEABLE,   Reserv, UNCACHED_UNBUFFERED_XN},
  {"RebootEscrow",       0x81FF0000, 0x00010000, AddMem,  MEM_RES, UNCACHEABLE,   Reserv, UNCACHED_UNBUFFERED_XN},
  {"Audio Mem",          0x94100000, 0x00300000, AddMem,  MEM_RES, UNCACHEABLE,   Reserv, UNCACHED_UNBUFFERED_XN},
  {"AudioDSP",           0x89000000, 0x00600000, AddMem,  MEM_RES, UNCACHEABLE,   Reserv, UNCACHED_UNBUFFERED_XN},

  // Free DRAM for DarwinBoot kernel window
  {"High RAM",           0x85400000, 0x10000000, AddMem,  SYS_MEM, SYS_MEM_CAP, Conv,   WRITE_BACK_XN},

  // Display framebuffer (logobuffer)
  {"Display Reserved",   0x9E000000, 0x00500000, AddMem,  MEM_RES, SYS_MEM_CAP,   Reserv, WRITE_THROUGH_XN},

  // Ramoops
  {"Ramoops",            0xFFF80000, 0x00040000, AddMem,  MEM_RES, UNCACHEABLE,   Reserv, UNCACHED_UNBUFFERED_XN},

  // Peripherals
  {"GICD",               0x10000000, 0x00020000, AddDev,  MMAP_IO, UNCACHEABLE,   MmIO,   NS_DEVICE},
  {"GICR",               0x10040000, 0x00100000, AddDev,  MMAP_IO, UNCACHEABLE,   MmIO,   NS_DEVICE},
  {"UART1",              0x200B0000, 0x00010000, AddDev,  MMAP_IO, UNCACHEABLE,   MmIO,   NS_DEVICE},
  {"SDHCI",              0x201A0000, 0x00001000, AddDev,  MMAP_IO, UNCACHEABLE,   MmIO,   NS_DEVICE},
  {"DPU",                0x31000000, 0x00002000, AddDev,  MMAP_IO, UNCACHEABLE,   MmIO,   NS_DEVICE},
  {"DSI",                0x31100000, 0x00001000, AddDev,  MMAP_IO, UNCACHEABLE,   MmIO,   NS_DEVICE},
  {"GPIO",               0x641B0000, 0x00010000, AddDev,  MMAP_IO, UNCACHEABLE,   MmIO,   NS_DEVICE},
  {"EIC",                0x641000A0, 0x00000020, AddDev,  MMAP_IO, UNCACHEABLE,   MmIO,   NS_DEVICE},
  {"PMIC SPI",           0x64200000, 0x00010000, AddDev,  MMAP_IO, UNCACHEABLE,   MmIO,   NS_DEVICE},
  {"Timer",              0x64470000, 0x00000040, AddDev,  MMAP_IO, UNCACHEABLE,   MmIO,   NS_DEVICE},
  {"pinctrl",            0x64710000, 0x00010000, AddDev,  MMAP_IO, UNCACHEABLE,   MmIO,   NS_DEVICE}
};

VOID
GetMemoryMap (
  OUT EFI_MEMORY_REGION_DESCRIPTOR **MemoryDescriptor,
  OUT UINT8                         *MemoryDescriptorCount
  )
{
  *MemoryDescriptor      = gMemoryDescriptor;
  *MemoryDescriptorCount = ARRAY_SIZE (gMemoryDescriptor);
}