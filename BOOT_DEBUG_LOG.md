# Boot Debug Log — hawaii / UMS9230

Data: 2026-11-17
Objetivo: Bootar UniXNU (UEFI → XNU) no Moto E32 (hawaii / UMS9230 / T606)

## Resumo do estado atual

O BootShim funciona (copia UEFI FD para 0x80800000, salta para o SEC).
O SEC assembly hook funciona (pinta ciano no framebuffer).
O SEC C code NÃO roda (magenta nunca aparece, device não reseta).

Tela: metade verde (ciano), metade logo Motorola (framebuffer não totalmente pintado).

## Fluxo de boot esperado

```
cboot (U-Boot) → boot_a (boot.img)
  → BootShim (ARM64 Image, magic ARMd @ 0x38)
    → copia UEFI FD (4MB) para 0x80800000
    → salta para 0x80800000 (SEC entry)
      → _ModuleEntryPoint (assembly)
        → PlatformAssemblyInitialize (pinta CIANO)
        → desabilita SPAN (SCTLR_EL1)
        → ArmEnableVFP (CPACR_EL1.FPEN)
        → SetupExceptionLevel1/2 (VBAR)
        → setup stack (SP = 0x80480000 + 0x40000)
        → chama SecEntry (C code)
          → ArmDisableDataCache
          → ArmInvalidateInstructionCache
          → ArmEnableInstructionCache
          → InvalidateDataCacheRange (stack + FD)
          → ArmWriteVBar (SecVectorTable)
          → chama SecMain
            → PlatformInitialize (pinta MAGENTA + PSCI reset)
            → SerialPortInitialize
            → InitializeMemory (MMU + HOB)
            → PlatformPeim
            → DecompressFirstFv
            → LoadDxeCoreFromFv
              → DXE Core
                → CpuDxe, ArmGicDxe, TimerDxe, RamManagerDxe, DtPlatformDxe
                → HawaiiBringupDxe (reseta pro Android no EndOfDxe)
```

## Tentativas e resultados

### 9. UART removido do SEC (BLOQUEADOR RESOLVIDO)
- **Problema**: `HawaiiPutc()` em `PlatformInitialize()` acessava UART1 (0x200B0000) sem clock/power init
- **Resultado**: external abort → travamento no SEC C code
- **Fix**: removido `HawaiiPutc()` de `PlatformInitialize()`, desabilitado `UartPutc()` em `SerialPortWrite()` com `#if !UART_DISABLED`
- **Resultado**: **UEFI RODANDO!** Texto aparece na tela

### 10. HawaiiPayloadDxe adicionado (ramdisk block device)
- **Driver**: lê FDT em 0x82000000, encontra `/chosen/linux,initrd-start/-end`
- **Publica**: payload FAT como read-only block device (512-byte blocks)
- **Resultado atual**: BDS mostra "Updating MemoryMapp... RegionStart: 0x011000..."
  e "Failed to Configuration ~MMUL?~ SElinux - Invalid ..."
- **Análise**: O BDS está rodando, processando configurações de memória.
  "Failed to Configuration SElinux" = SecurityStubDxe não consegue configurar SELinux (esperado sem Secure Boot).
  O "Invalid" pode ser do BDS não encontrando boot option válido (payload FAT não montado ainda).
- **Próximo passo**: verificar se HawaiiPayloadDxe encontrou o initrd e publicou o block device.
  Se não, o BDS não encontra o UniXNU.efi e mostra "Invalid Boot Option".

### 8. BootShim com VFP enable (CPACR_EL1.FPEN)
- **BootShim**: adiciona `mrs x7, CPACR_EL1; orr x7, x7, #(3<<20); msr CPACR_EL1, x7; isb`
- **Objetivo**: pré-habilitar VFP para evitar crash em ArmEnableVFP
- **Resultado**: magenta apareceu → VFP era o problema ✅

### 1. BootShim original (com mov x4, x1 extra)
- **Problema**: 3 instruções em _Head desalinhavam o header ARM64
- **Resultado**: bootloop (UDF #0 em 0x00)
- **Fix**: removido `mov x4, x1` extra, mantido `adr x1, _Payload` em 0x00

### 2. assemble_bootshim_fd.py com header sintético
- **Problema**: prependia header ARM64 zerado (0x00000000 = UDF #0)
- **Resultado**: bootloop
- **Fix**: removido header sintético, BootShim já contém header ARM64 válido

### 3. BootShim sem .ltorg
- **Problema**: literal pool (FD_BASE/FD_SIZE) em _Payload (0x70), UEFI FD anexado em 0x80
- **Resultado**: BootShim copiava literal pool em vez do UEFI FD
- **Fix**: adicionado `.ltorg` antes de _Payload (literal pool em 0x70-0x7f, _Payload em 0x80)

### 4. UEFI firmware incompleto (sem SEC/PEI/DXE)
- **Problema**: FDF só tinha DXE drivers, sem SEC/PEI/FVMAIN_COMPACT
- **Resultado**: UEFI sem entry point, crash imediato
- **Fix**: reescrito hawaii.dsc/hawaii.fdf seguindo bbkA2 (SEC no FVMAIN_COMPACT, DXE no FVMAIN)

### 5. PlatformSecLib com cntvct_el0 (2s hold)
- **Assembly**: ciano + cntvct_el0 2s hold
- **C code**: magenta + cntvct_el0 2s hold
- **Resultado 1º boot**: ciano → magenta ✅ (C code rodou!)
- **Resultado boots seguintes**: apenas ciano ❌ (cntvct_el0 não roda após reset)
- **Fix**: removido cntvct_el0, substituído por busy loop simples

### 6. PlatformSecLib sem hold (busy loop + segundo paint no assembly)
- **Assembly**: ciano + busy loop 73728 + magenta
- **C code**: magenta + busy loop + PSCI reset
- **Resultado**: apenas ciano ❌ (assembly não completa segundo paint)
- **Hipótese**: crash no busy loop ou no segundo paint

### 7. PlatformSecLib simplificado (apenas ciano no assembly, magenta + PSCI no C)
- **Assembly**: apenas ciano, retorna
- **C code**: magenta + PSCI SYSTEM_RESET (smc #0, x0=0x84000000)
- **Resultado**: apenas ciano ❌ (C code não roda)
- **Conclusão**: crash entre assembly hook return e PlatformInitialize

### 8. BootShim com VFP enable (CPACR_EL1.FPEN)
- **BootShim**: adiciona `mrs x0, CPACR_EL1; orr x0, x0, #(3<<20); msr CPACR_EL1, x0; isb`
- **Objetivo**: pré-habilitar VFP para evitar crash em ArmEnableVFP
- **Resultado**: [PENDENTE — não flashado ainda]

## Análise do crash

O crash ocorre entre:
1. `PlatformAssemblyInitialize` retorna (ciano pintado ✅)
2. `_ModuleEntryPoint` continua:
   - `EL1_OR_EL2(x0)` → le CurrentEL
   - Desabilita SPAN (SCTLR_EL1)
   - `ArmEnableVFP` (CPACR_EL1)
   - `SetupExceptionLevel1/2` (VBAR)
   - Setup stack (SP = 0x80480000 + 0x40000)
   - Clear stack (escreve zeros em 0x80480000-0x804C0000)
3. `SecEntry` (C code):
   - Cache operations
   - VBAR write
4. `SecMain`:
   - `PlatformInitialize` (magenta) ← NUNCA CHEGA AQUI

## Hipóteses do crash

### H1: ArmEnableVFP falha
- UMS9230 pode precisar de configuração específica de CPACR_EL1
- Fix tentado: pré-habilitar VFP no BootShim (tentativa 8)

### H2: SetupExceptionLevel1/2 falha
- VBAR write pode falhar se VBAR não estiver alinhado
- Verificar se SecVectorTable está alinhado

### H3: Stack clear corrompe algo
- Stack em 0x80480000, BootShim source termina em 0x80480090 (144 bytes)
- Overlap de 0x90 bytes entre stack e BootShim source
- Mas BootShim já terminou, não deveria importar

### H4: InvalidateDataCacheRange falha
- Invalida 0x80480000 (stack, 0x40000) e 0x80800000 (FD, 0x400000)
- Pode falhar se a região não estiver mapeada (MMU off)

### H5: Framebuffer stride errado
- Tela metade verde = 1,152,000 pixels / 1600 = 720 linhas
- Mas só metade da tela visível é pintada
- Framebuffer pode ser 32bpp (4 bytes/pixel), não 16bpp (2 bytes/pixel)
- Stride real pode ser 1600*4 = 6400 bytes, não 1600*2 = 3200 bytes
- Isso explica a meia tela, mas não explica o crash do C code

## Próximos passos

1. **Flashar tentativa 8** (BootShim com VFP enable)
   - Se magenta aparecer + reset = VFP era o problema ✅
   - Se ficar verde = VFP não era o problema, investigar H2/H3/H4

2. **Se H1 falhar**: modificar ModuleEntryPoint.S do SiliciumPkg para pular ArmEnableVFP
   - (não ideal, modifica upstream)

3. **Se H1 falhar**: adicionar stage markers no assembly após cada passo
   - Após SPAN disable: pintar de outra cor
   - Após VFP enable: pintar de outra cor
   - Após exception setup: pintar de outra cor
   - Após stack setup: pintar de outra cor

4. **Corrigir framebuffer stride**: verificar se é 16bpp ou 32bpp
   - mibde div: ler registradores DPU em 0x31000000
   - Tentar ambas as resoluções

## Endereços-chave

| Item | Endereço | Tamanho |
|------|----------|---------|
| BootShim (kernel load) | 0x80080000 | 144 bytes |
| UEFI FD_BASE | 0x80800000 | 0x400000 (4MB) |
| Stack | 0x80480000 | 0x40000 (256KB) |
| SEC Heap | 0x80680000 | 0x100000 (1MB) |
| MMU PT | 0x80780000 | 0x40000 |
| DXE Heap | 0x80C00000 | 0x13D0000 (~19.9MB) |
| VarStore | 0x81FD0000 | 0x20000 |
| FDT | 0x82000000 | 0x100000 |
| Framebuffer | 0x9e000000 | 0x500000 (5MB) |
| Ramoops | 0xfff80000 | 0x40000 |
| GIC D | 0x10000000 | 0x20000 |
| GIC R | 0x10040000 | 0x100000 |
| UART1 | 0x200b0000 | 0x10000 |

## Hash da imagem atual (não flashada)

SHA-256: 60c89f88e73c89183079a3038dd65f3ff9fedff57abb079e5063819c65eaec3c
BootShim: 144 bytes (com VFP enable)
UEFI FD: 4194304 bytes
Total: 4194448 bytes (0x400090)

## Referências

- `../unixnu-eebbk-a2_x2-ums512` — UMS512/T610, mesma família, UEFI funcional
- `../unixnu-core` — UniXNU core (profiles, UniXNUPkg, DarwinBoot)
- `https://github.com/Project-Silicium/Mu-Silicium` — SiliciumPkg (SEC, DXE core)
- `https://github.com/ampekk/UniXNU-hotdog` — iPhone X iOS 16.7.16 (referência arm64)