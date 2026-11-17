# Progresso - Inicializar UniXNU no Moto E32 (hawaii/UMS9230)

## Fluxo correto (segundo documentação UniXNU)

```
Bootloader UNISOC/Android → boot.img (cabeçalho Android válido)
  → BootShim ARM64 (copia UEFI FD para memória, salta para ele)
  → UEFI + drivers de plataforma
  → Encontra payload FAT no volume
  → DarwinBoot lê kernel.macho, prepara argumentos, inicia XNU
```

O XNU Mach-O NÃO é carregado pelo bootloader Android. É carregado pelo DarwinBoot dentro do UEFI.

## Problemas identificados e status

| # | Problema | Status | Ação |
|---|----------|--------|------|
| 1 | BootShim incorreto (não copia FD, destrói x0) | ❌ Pendente | Substituir por modelo Mu-Silicium |
| 2 | Endereço UEFI não confirmado (0x80800000) | ⚠️ Parcial | Dados coletados: fdtdtb, iomem, boot_b original |
| 3 | mkbootimg.py incorreto (campos v2 desalinhados) | ❌ Pendente | Usar pack_and_sign_boot.py do E32 |
| 4 | Payload 192 MiB grande demais (partição = 64 MiB) | ❌ Pendente | Criar payload FAT 4-8 MiB |
| 5 | DTB inconsistente (2 GiB vs 4 GB real) | ❌ Pendente | Usar DTB real do dispositivo |
| 6 | Sem AVB footer | ❌ Pendente | Assinar com pack_and_sign_boot.py |

## Dados coletados do dispositivo (em extracted/)

| Arquivo | Tamanho | Conteúdo |
|---------|---------|----------|
| `hawaii-live.dtb` | 306.474 B | DTB real do dispositivo |
| `boot_b-original.img` | 64 MiB | boot_b stock (kernel Linux + ramdisk) |
| `uboot_b.img` | 3 MiB | U-Boot do dispositivo |
| `cmdline.txt` | 1.484 B | Linha de comando do kernel Android |
| `iomem.txt` | 4.537 B | Mapa de memória I/O |

## Próximos passos

1. Analisar boot_b original para entender estrutura do cabeçalho Android v2
2. Baixar pack_and_sign_boot.py do repo motorola-moto-e32-root
3. Corrigir BootShim (modelo Mu-Silicium)
4. Criar payload FAT pequeno (4-8 MiB)
5. Empacotar: BootShim+UEFI como "kernel", payload FAT como ramdisk
6. AVB-assinar
7. Gravar via dd com root (fastboot flash não funciona)
8. Testar boot

## Estado atual do dispositivo

- Slot b: Android original (funcionando)
- Slot a: boot.img do UniXNU gravado via dd (VERIFY OK) - não bootou
- Bootloader: desbloqueado (flash.locked=0, verifiedbootstate=orange)
