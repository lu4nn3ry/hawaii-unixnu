# Conceito: Menu UEFI Dual-Boot (UniXNU + Android)

Data: 2026-11-17
Status: Conceitual — não implementado ainda.

## Visão geral

Criar um menu UEFI (`HawaiiBootMenu.efi`) dentro do firmware volume que apareça
mesmo quando o payload FAT do UniXNU não for encontrado. O menu terá três opções:

1. **Boot UniXNU** — Slot A, inicia UniXNU.efi + DarwinBoot
2. **Android** — Slot B, seleciona boot_b no bootloader e reinicia
3. **UEFI Shell** — acesso ao shell para diagnóstico

## Arquitetura

O `HawaiiBootMenu.efi` deve:
- Ser uma aplicação UEFI independente dentro do FV (não depende do payload FAT)
- Usar `EFI_SIMPLE_TEXT_IN_PROTOCOL` + `EFI_SIMPLE_TEXT_OUT_PROTOCOL` para input/output
- Usar `EFI_BLOCK_IO_PROTOCOL` para acessar a partição `misc` (metadados A/B)
- Usar `gRT->ResetSystem()` para reiniciar após trocar o slot

## Seleção de slot Android (boot_b)

O Android usa metadados A/B na partição `misc` para indicar qual slot bootar:
- Slot ativo (a ou b)
- Prioridade
- Tentativas restantes
- Estado de boot bem-sucedido

O comando `fastboot set_active b` é a referência de comportamento a reproduzir no UEFI.

### Procedimento Android B:
1. Encontrar partição `misc` via `EFI_BLOCK_IO_PROTOCOL`
2. Ler metadados A/B (boot control structure)
3. Validar estrutura e CRC
4. Selecionar slot B, preservando demais dados
5. Confirmar gravação por leitura
6. Executar `ResetSystem()`

### Aviso:
- **Não escrever diretamente em `misc` com offset presumido.**
- Primeiro comparar backup da partição com estado produzido por `fastboot set_active b`.
- O layout concreto da partição `misc` precisa ser confirmado no cboot da Motorola.

## Estado atual do firmware

### O que funciona:
- `UniXNUDxe` registra `UniXNU.efi` como Boot#### option
- `HawaiiPayloadDxe` descobre o ramdisk via FDT `/chosen/linux,initrd-start/-end`
- `UniXNURamDiskDxe` publica o payload FAT como block device
- DiskIoDxe + FatPkg montam o volume FAT
- BDS inicia o boot manager

### O que falta:
- **Input físico**: touch (Goodix gt9xx) ou GPIO keys (Volume +/-, Power) ainda não implementados
- **SDHCI driver**: `SdhciBlock` ainda como planejado no porting.toml
- **Menu visual**: BDS ainda aponta para UEFI Shell, não para um menu customizado
- **Confirmação**: verificar se cboot coloca `linux,initrd-start/-end` no FDT em execução

## Ordem de implementação recomendada

1. Confirmar no display se `UniXNUDxe` criou o Boot####
2. Exibir valores reais de `linux,initrd-start/end` e resultado do `UniXNURamDiskDxe`
3. Criar `HawaiiBootMenu.efi` no firmware volume (independente do payload)
4. Implementar seletor Android B usando metadados A/B validados
5. Integrar teclas físicas (GPIO keys ou touch) ao menu

## Referências

- [Android A/B OTA](https://source.android.com/docs/core/ota/ab)
- [Android boot control (AOSP)](https://android.googlesource.com/platform/external/u-boot/+/92872ef6932c2205b2783fc4449a8ce00fa9d2f9/include/android_bl_msg.h)
- [UniXNU boot chain](https://unixnu.com/concepts/boot-chain)
- [UniXNU firmware integration](https://unixnu.com/porting/uefi-firmware)