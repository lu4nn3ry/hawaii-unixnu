/* BootShim.S - Trampoline de boot para UniXNU no Moto E32 (UMS9230/T606)
 *
 * Fluxo:
 *   1. O bootloader Android carrega este arquivo como "kernel" no boot.img
 *   2. O BootShim copia o firmware UEFI (anexado após _Payload) para FD_BASE
 *   3. Salta para a entrada do UEFI em FD_BASE
 *
 * Baseado no BootShim do Mu-Silicium, adaptado para o UMS9230.
 *
 * Defines necessários (passados via linha de comando):
 *   -DFD_BASE=0x80800000   endereço de destino do UEFI
 *   -DFD_SIZE=0x400000     tamanho do firmware UEFI (4 MiB)
 *   -DREQUIRES_KERNEL_HEADER=1  incluir cabeçalho ARM64 com magic ARMd
 */

     .text
     .align  4
     .global _Head
 _Head:
     /* code0 (0x00) + code1 (0x04): ARM64 Image header entry.
      * adr x1, _Payload sets the firmware address; b _Start jumps to
      * the copy loop. These two instructions must occupy 0x00-0x07 so
      * text_offset lands at 0x08 and the ARMd magic at 0x38. */
     adr     x1, _Payload      /* x1 = endereço do firmware UEFI anexado */
     b       _Start            /* Pular para o código real */

#if REQUIRES_KERNEL_HEADER == 1
_StackBase:
    .quad   FD_BASE           /* Text Offset */

_StackSize:
    .quad   FD_SIZE + (_Payload - _Head)  /* Image Size + comprimento do shim */
    .quad   0                 /* Flags */
    .quad   0                 /* Reserved */
    .quad   0                 /* Reserved */
    .quad   0                 /* Reserved */
    .ascii  "ARM\x64"         /* ARM64 Magic */
    .long   0                 /* Reserved */
#endif

_Start:
    mov     x4, x1            /* x4 = endereço do payload (FDT ou UEFI) */

    /* Habilita VFP/NEON antes de saltar pro SEC (evita crash em ArmEnableVFP).
     * Usa x7 para não destruir x0 (endereço do FDT do bootloader). */
    mrs     x7, CPACR_EL1
    orr     x7, x7, #(3 << 20)      /* FPEN = 0b11 (full access) */
    msr     CPACR_EL1, x7
    isb

    ldr     x5, =FD_BASE      /* x5 = endereço de destino do UEFI */
    cmp     x4, x5            /* Se já está em FD_BASE, não precisa copiar */
    beq     _Entry            /* Pular diretamente para a entrada */
    ldr     x6, =FD_SIZE      /* x6 = tamanho a copiar */

_CopyLoop:
    ldp     x2, x3, [x4], #16 /* Carregar 16 bytes do payload */
    stp     x2, x3, [x5], #16 /* Armazenar 16 bytes em FD_BASE */
    subs    x6, x6, #16       /* Decrementar contador */
    b.ne    _CopyLoop         /* Continuar copiando */
    ldr     x5, =FD_BASE      /* Endereço de entrada do UEFI */

_Entry:
    br      x5                /* Saltar para o UEFI */

 _Dead:
     b       _Dead             /* Loop infinito em caso de erro */

     .ltorg                      /* flush literal pool (FD_BASE/FD_SIZE) before _Payload */

     .text
     .align  4

 _Payload:
     /* O firmware UEFI (SILICIUM_UEFI.fd) é anexado aqui pelo empacotador */
