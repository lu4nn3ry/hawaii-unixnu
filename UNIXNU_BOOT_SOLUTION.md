# Solução para inicializar o UniXNU no Moto E32 (hawaii / UMS9230 / T606)

## Resumo executivo

O fluxo correto do UniXNU usa o **boot.img do Android** como transporte:

1. Bootloader Android carrega **BootShim** (pequeno programa ARM64)
2. BootShim copia o firmware UEFI para memória e transfere controle para ele
3. UEFI encontra um volume FAT com o payload do UniXNU
4. DarwinBoot lê `kernel.macho`, prepara argumentos e inicia o XNU

O Android não executa o Mach-O diretamente — executa o BootShim. O XNU é carregado depois pelo DarwinBoot.

## Problemas encontrados e correções

### Problema 1 — BootShim incorreto (`uefi-hawaii/BootShim/BootShim.S`)

O BootShim atual destrói `x0` (endereço do FDT) e apenas pula para `FD_BASE` sem copiar o firmware UEFI anexado.

**Correção:** Substituir pelo modelo do Mu-Silicium que:
- Preserva `x0` (endereço do FDT recebido)
- Localiza `_Payload` para encontrar o firmware anexado
- Copia o FD para o endereço configurado (`FD_BASE`)
- Salta para a entrada do UEFI
- O campo de tamanho deve incluir BootShim + firmware: `FD_SIZE + (_Payload - _Head)`

### Problema 2 — Endereço UEFI não confirmado

`board.toml` configura `FD_BASE = 0x80800000`, `FD_SIZE = 0x400000`, mas esses valores não foram validados no U-Boot do Moto E32.

**Ação:** Extrair o mapa de memória real do dispositivo antes de gravar qualquer imagem.

### Problema 3 — mkbootimg.py monta cabeçalho Android incorretamente

O script atual escreve campos em posições incompatíveis com AOSP v2. Ex: coloca `ramdisk_size` onde deveria estar `kernel_addr`, desloca campos seguintes, e coloca a linha de comando fora da posição reservada.

**Correção:** Usar o empacotador AOSP/Mu-Silicium ou preservar o cabeçalho original do boot_b do Moto E32.

### Problema 4 — Payload muito grande

`board.toml` define `size_mib = 192`, mas a partição boot do Moto E32 tem 64 MiB.

**Correção:** Reduzir para 4-8 MiB para o primeiro teste.

### Problema 5 — Device tree inconsistente

`dts/hawaii.dts` declara memória como 2 GiB (`0x80000000`), mas o aparelho tem 4 GB físicos.

**Correção:** Extrair memória real do DTB original do dispositivo.

## Fluxo de empacotamento recomendado

```
Cabeçalho Android original v2 (preserva endereços, página, parâmetros do Moto E32)
Kernel ARM64: BootShim + UEFI FD (imagem sem gzip, assinatura ARMd)
Ramdisk: payload FAT do UniXNU (volume pequeno, 4-8 MiB)
DTB original do Moto E32 (preservado inicialmente)
AVB footer (gerado pelo procedimento já testado no E32)
```

## Próximos passos

1. Extrair dados reais do aparelho: cabeçalho, DTB, mapa de memória, endereço de execução
2. Corrigir BootShim usando código Mu-Silicium
3. Construir UEFI mínimo para UMS9230 (UART, memória, GIC, timer)
4. Criar payload FAT pequeno
5. Empacotar usando `pack_and_sign_boot.py` do projeto de root do Moto E32
6. Primeiro teste com `fastboot boot` (se disponível)

## Comandos para extrair dados do dispositivo (somente leitura)

```
adb shell getprop ro.boot.slot_suffix
adb shell getprop ro.product.device
adb shell getprop ro.board.platform
adb shell cat /proc/cmdline
adb shell cat /proc/meminfo
adb shell cat /proc/iomem
adb pull /sys/firmware/fdt hawaii-live.dtb
```

**Não gravar o novo boot.img ainda.** O `fastboot flash` é bloqueado pelo mecanismo de download do aparelho.
