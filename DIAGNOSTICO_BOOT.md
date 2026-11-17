# Diagnóstico de Boot — Moto E32 / UMS9230 / hawaii

Data: 2026-11-17
Estado: boot_a grava com bootloop. BootShim corrigido, mas UEFI firmware incompleto.

## O que está FUNCIONANDO

1. **BootShim.S** — corrigido e validado:
   - `adr x1, _Payload` em 0x00 (code0)
   - `b _Start` em 0x04 (code1)
   - `text_offset = 0x80800000` em 0x08
   - `image_size = 0x400080` em 0x10
   - `ARMd` magic em 0x38
   - `.ltorg` antes de `_Payload` (literal pool em 0x70-0x7f, _Payload em 0x80)
   - Verificado com `aarch64-linux-gnu-objdump -d`

2. **Empacotamento do boot.img** — `scripts/pack_unixnu_boot.py`:
   - Cabeçalho Android v2 preservado do boot_b original
   - kernel = BootShim + UEFI FD (4 MB, ARM64 Image com magic ARMd)
   - ramdisk = payload FAT (8 MB)
   - DTB original preservado
   - AVB SHA256_RSA4096 assinado (rollback index 2)
   - Hash verificado no device (dd read-back = host sha256)

3. **Flash e slot** — `scripts/flash_boot_a.py`:
   - dd via root (mali_kroot CVE-2021-28663) para /dev/block/by-name/boot_a
   - VERIFY OK (hash 9d201f85... conferido)
   - fastboot set_active a confirmado

4. **Repositório de referência** — `../unixnu-eebbk-a2_x2-ums512`:
   - UMS512/T610, mesma família Unisoc
   - FDF/DSC completo e funcional
   - SEC, PEI, DXE core, UniXNU, DarwinBoot, RamDiskDxe, GOP, SDHCI

## O que está QUEBRADO — UEFI firmware

O firmware UEFI (`uefi-hawaii/`) é um esqueleto mínimo que **não pode bootar**.

### Problema 1: FDF sem estrutura SEC/PEI/DXE

`uefi-hawaii/Platforms/Unisoc/hawaiiPkg/hawaii.fdf` atual:
```ini
[Files SILICIUM_UEFI]
  INF  MdeModulePkg/Universal/BdsDxe/BdsDxe.inf
  INF  MdeModulePkg/Universal/ConsoleSplitterDxe/ConsoleSplitterDxe.inf
  ... (apenas DXE drivers, sem SEC/PEI)
```

Referência UMS512 (`bbkA2.fdf`) correta:
```ini
[FD.SILICIUM_UEFI]
BaseAddress   = $(FD_BASE)
Size          = $(FD_SIZE)
...

[FV.FvMain]
  !include Include/APRIORI.inc
  !include Include/DXE.inc
  INF SiliciumPkg/Drivers/RamManagerDxe/RamManagerDxe.inf
  INF EmbeddedPkg/Drivers/DtPlatformDxe/DtPlatformDxe.inf
  INF bbkA2Pkg/Drivers/BbkA2PayloadDxe/BbkA2PayloadDxe.inf
  INF UniXNUPkg/Application/UniXNU/UniXNU.inf
  INF UniXNUPkg/Driver/UniXNUDxe/UniXNUDxe.inf
  INF UniXNUPkg/Driver/UniXNURamDiskDxe/UniXNURamDiskDxe.inf
  INF DarwinBootPkg/Driver/DarwinBoot.inf
  INF ShellPkg/Application/Shell/Shell.inf

[FV.FVMAIN_COMPACT]
  INF SiliciumPkg/Sec/Sec.inf
  FILE FV_IMAGE = ... { SECTION FV_IMAGE = FVMAIN }
  !include SiliciumPkg/Common.fdf.inc
```

### Problema 2: DSC sem inicialização de plataforma

`uefi-hawaii/Platforms/Unisoc/hawaiiPkg/hawaii.dsc` atual:
- Sem `[PcdsFixedAtBuild]` (memory base, stack, debug level)
- Sem `!include UMS9230Pkg/UMS9230Pkg.dsc.inc`
- Sem `MemoryMapLib`, `PlatformSecLib`, `UniXNULib`
- Sem `[Components]` para UniXNU, DarwinBoot, RamDiskDxe

### Problema 3: Módulos UniXNU ausentes

Faltam no FDF/DSC:
- `UniXNUPkg/Application/UniXNU/UniXNU.inf` — menu de boot
- `UniXNUPkg/Driver/UniXNUDxe/UniXNUDxe.inf` — boot option registrar
- `UniXNUPkg/Driver/UniXNURamDiskDxe/UniXNURamDiskDxe.inf` — descobre payload FAT
- `DarwinBootPkg/Driver/DarwinBoot.inf` — XNU loader

### Problema 4: Platform-specific drivers ausentes

Faltam (precisam ser escritos para UMS9230):
- `MemoryMapLib` — mapa de memória do board (reserved-memory, framebuffer, etc.)
- `PlatformSecLib` — hooks SEC (UART, stage markers)
- `SprdGopDxe` ou `SimpleFbDxe` — GOP driver (framebuffer 0x9e000000)
- `SprdSdhciMmcHostDxe` — eMMC SDHCI (0x201a0000)
- `PayloadDxe` — publica initrd como block device
- `BringupDxe` — probe de bring-up (dump memory map + reset)

### Problema 5: Includes ausentes

Faltam:
- `Include/APRIORI.inc` — DXE dependency list
- `Include/DXE.inc` — DXE driver list
- `SiliciumPkg/Common.fdf.inc` — regras FDF (SEC, DXE_DRIVER, etc.)
- `SiliciumPkg/SiliciumPkg.dsc.inc` — DSC base (library classes, PCDs)
- `UMS9230Pkg/UMS9230Pkg.dsc.inc` — SoC-specific DSC

## Causa do bootloop

O bootloader carrega BootShim+UEFI FD para 0x80080000, salta para 0x80080000.
BootShim copia o UEFI FD (4 MB) para 0x80800000 e salta para 0x80800000.
O UEFI em 0x80800000 **não tem SEC entry point** — o primeiro byte do FV
não é código válido de entry. O CPU executa lixo ou trava, watchdog reseta → bootloop.

## Referência para o especialista

Clone: `github.com/woshimaniubi8/unixnu-eebbk-a2_x2-ums512` (UMS512, mesma família)

Arquivos-chave para adaptar:
- `uefi/Platforms/Unisoc/bbkA2Pkg/bbkA2.dsc` → hawaii.dsc
- `uefi/Platforms/Unisoc/bbkA2Pkg/bbkA2.fdf` → hawaii.fdf
- `uefi/Platforms/Unisoc/bbkA2Pkg/Include/APRIORI.inc` → copiar
- `uefi/Platforms/Unisoc/bbkA2Pkg/Include/DXE.inc` → adaptar
- `uefi/Silicon/Unisoc/UMS512Pkg/UMS512Pkg.dsc.inc` → UMS9230Pkg.dsc.inc
- `uefi/Resources/Configs/bbk-a2.toml` → hawaii.toml

UniXNU core (para PACKAGES_PATH):
- `github.com/UniXNU/UniXNU` — package/UniXNUPkg, drivers/DarwinBoot
- `github.com/UniXNU/uefi-sheng` — Silicon/Silicium (SEC, DXE core, drivers)

## Endereços verificados (do device)

- System RAM: 0x80000000-0x853effff (primeiro segmento ~84 MB)
- Kernel code (Android): 0x80080000-0x813effff
- Framebuffer/logobuffer: 0x9e000000 (1600x720, 32bpp)
- UEFI FD_BASE: 0x80800000 (8 MB into RAM, acima do kernel)
- UEFI FD_SIZE: 0x400000 (4 MB)
- SDHCI: 0x201a0000
- UFS: 0x20200000
- UART1: 0x200b0000 (115200n8, console=ttyS1)
- GIC: 0x10000000
- GPU: 0x23100000
- DPU: 0x31000000
- DSI: 0x31100000
- PMIC SPI: 0x64200000

## Próximo passo

1. Adaptar bbkA2.dsc/fdf para hawaii (UMS9230)
2. Escrever MemoryMapLib para o mapa de memória do hawaii
3. Escrever PlatformSecLib (UART1 init)
4. Adaptar UMS512Pkg.dsc.inc para UMS9230 (GIC, timer, UART bases)
5. Adicionar módulos UniXNU ao FDF/DSC
6. Build com `./unixnu build firmware --uefi ../uefi-hawaii`
7. Re-empacotar boot.img com o novo FD
8. Flash boot_a e testar