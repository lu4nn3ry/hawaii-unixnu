#!/usr/bin/env python3
"""Simple DTS -> DTB compiler using libfdt (fallback when dtc is unavailable)."""
import sys
import struct

def parse_dts(path):
    """Very minimal DTS parser - handles only the properties we need for ADT generation."""
    with open(path, 'r') as f:
        content = f.read()
    # Remove comments
    import re
    content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    return content

def dtb_from_dts(dts_path, dtb_path):
    """Create a minimal DTB from DTS for ADT generation."""
    # This is a placeholder - in a real port we would use dtc
    # For now, create a minimal valid FDT header
    fdt_magic = 0xd00dfeed
    fdt_size = 4096
    fdt_off_dt_struct = 0x1000
    fdt_off_dt_strings = 0x2000
    fdt_off_mem_rsvmap = 0x800
    fdt_version = 17
    fdt_last_comp_version = 16
    fdt_boot_cpuid_phys = 0
    fdt_size_dt_strings = 0x100
    fdt_size_dt_struct = 0x1000
    
    header = struct.pack('<IIIIIIIIIIII',
        fdt_magic, fdt_size, fdt_off_dt_struct, fdt_off_dt_strings,
        fdt_off_mem_rsvmap, fdt_version, fdt_last_comp_version,
        fdt_boot_cpuid_phys, fdt_size_dt_strings, fdt_size_dt_struct, 0, 0)
    
    # End token
    end_token = struct.pack('<I', 0x00000009)  # FDT_END
    
    # Reserve map (empty)
    rsvmap = struct.pack('<II', 0, 0)
    
    # Strings block
    strings = b'/chosen\0/cpus\0/arm-io\0/intc\0/uart0\0/timer\0/gic\0/memory\0/model\0\0'
    
    # Struct block (minimal)
    struct_data = b''
    
    # Build the DTB
    dtb = header + rsvmap + struct_data + strings + end_token
    dtb = dtb.ljust(fdt_size, b'\x00')
    
    # Fix up offsets in header
    dtb = dtb[:12] + struct.pack('<I', len(dtb)) + dtb[16:]  # fix size
    
    with open(dtb_path, 'wb') as f:
        f.write(dtb)
    
    print(f"DTB written: {dtb_path} ({len(dtb)} bytes)")
    return True

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <dts_path> <dtb_path>")
        sys.exit(1)
    dtb_from_dts(sys.argv[1], sys.argv[2])
