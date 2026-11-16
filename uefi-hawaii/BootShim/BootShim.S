/* BootShim.S - cboot trampoline for hawaii (Moto E32 / UMS9230)
 *
 * Follows Mu-Silicium layout:
 *   https://unixnu.com/porting/uefi-firmware#mu-silicium-layout
 *
 * The stock bootloader places the firmware volume at FD_BASE and jumps
 * to this trampoline, which relocates EDK2 and transfers control to
 * the UEFI entry point.
 *
 * NOTE: Addresses (FD_BASE, kernel load address) are UNVERIFIED for
 * hawaii cboot. They must be measured from the vendor uboot.bin before
 * first flash attempt.
 */

.section .text
.global _start

_start:
    /* Save bootloader handoff state */
    mrs     x0, mpidr_el1
    mov     x1, x0

    /* Set up initial stack */
    adr     x2, stack_top
    mov     sp, x2

    /* Jump to EDK2 SEC entry point */
    /* FD_BASE is compiled in by mkbootimg/clang with -DFD_BASE=... */
    ldr     x3, =FD_BASE
    br      x3

.section .data
.align  4
stack_top:
    .zero   0x1000

.section .rodata
.align  4
FD_BASE:
    .quad   0x80800000   /* overridden at build time by -DFD_BASE= */
