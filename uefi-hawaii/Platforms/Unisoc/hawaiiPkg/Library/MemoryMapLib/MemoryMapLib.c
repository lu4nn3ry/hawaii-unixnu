/*
  Moto E32 (hawaii / UMS9230 / T606) memory map.

  Addresses from /proc/iomem on the live device and vendor DTS.
  All regions are non-overlapping. MemoryPeim/ValidateMemoryMap calls
  CpuDeadLoop on overlap, so every reserved region must be separated
  from conventional RAM by exact boundaries.

  Physical RAM: 0x80000000 - 0x17fffefff (4 GiB, but ~3.5 GiB usable)
  Vendor carve-outs (from DTS reserved-memory):
    WCN:       0x87000000, 0x001A0000
    AudioDSP:  0x89000000, 0x00600000
    Audio Mem: 0x94100000, 0x00300000
    Logobuffer: 0x9E000000, 0x00AB0000 (framebuffer)
    Ramoops:   0xFFF80000, 0x00040000
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

  // Vendor reserved regions (from DTS reserved-memory)
  {"DDRBIST",            0x80000000, 0x00001000, AddMem,  MEM_RES, UNCACHEABLE,   Reserv, UNCACHED_UNBUFFERED_XN},
  {"RebootEscrow",       0x81FF0000, 0x00010000, AddMem,  MEM_RES, UNCACHEABLE,   Reserv, UNCACHED_UNBUFFERED_XN},
  {"WCN Reserved",       0x87000000, 0x001A0000, AddMem,  MEM_RES, UNCACHEABLE,   Reserv, UNCACHED_UNBUFFERED_XN},
  {"AudioDSP",           0x89000000, 0x00600000, AddMem,  MEM_RES, UNCACHEABLE,   Reserv, UNCACHED_UNBUFFERED_XN},
  {"Audio Mem",          0x94100000, 0x00300000, AddMem,  MEM_RES, UNCACHEABLE,   Reserv, UNCACHED_UNBUFFERED_XN},

  // Free RAM regions (non-overlapping with reserved regions above)
  // 0x85400000 to 0x87000000 = 0x1C00000 (28 MB, before WCN)
  {"Free RAM Low A",     0x85400000, 0x01C00000, AddMem,  SYS_MEM, SYS_MEM_CAP, Conv,   WRITE_BACK_XN},
  // 0x871A0000 to 0x89000000 = 0x1E60000 (31.4 MB, between WCN and AudioDSP)
  {"Free RAM Low B",     0x871A0000, 0x01E60000, AddMem,  SYS_MEM, SYS_MEM_CAP, Conv,   WRITE_BACK_XN},
  // 0x89600000 to 0x94100000 = 0xAB00000 (171 MB, between AudioDSP and Audio Mem)
  {"Free RAM Mid",       0x89600000, 0x0AB00000, AddMem,  SYS_MEM, SYS_MEM_CAP, Conv,   WRITE_BACK_XN},
  // 0x94400000 to 0x9E000000 = 0x9C00000 (156 MB, between Audio Mem and framebuffer)
  {"Free RAM High A",    0x94400000, 0x09C00000, AddMem,  SYS_MEM, SYS_MEM_CAP, Conv,   WRITE_BACK_XN},

  // Display framebuffer (logobuffer, from DTS: 0xab0000)
  {"Display Reserved",   0x9E000000, 0x00AB0000, AddMem,  MEM_RES, SYS_MEM_CAP,   Reserv, WRITE_THROUGH_XN},

  // 0x9EAB0000 to 0xF4000000 = 0x5550000 (85.3 MB, after framebuffer)
  {"Free RAM High B",    0x9EAB0000, 0x05550000, AddMem,  SYS_MEM, SYS_MEM_CAP, Conv,   WRITE_BACK_XN},

  // Ramoops (persistent log)
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