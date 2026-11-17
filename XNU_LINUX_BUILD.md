# Build do kernel XNU no Linux (UniXNU)

## Descoberta

O UniXNU documenta oficialmente um método para compilar o kernel XNU fora do macOS,
utilizando uma toolchain exportada de um Mac. Não é obrigatório manter todo o
ambiente de compilação no macOS.

Fonte: https://unixnu.com/guide/build-kernel
Seções relevantes: "Local builds with exported inputs" e "Source and tree".

## Toolchain Linux oficial

O instalador oficial está em:

```
scripts/linux/setup-toolchain.py
```

Comando documentado:

```
sudo scripts/linux/setup-toolchain.py
scripts/linux/setup-toolchain.py --check
./unixnu build kernel
```

A toolchain inclui:

- Clang/LLVM modificado para recursos internos do XNU
- `ld64`, `libtool`, `nm` e `lipo` do `cctools-port`
- `mig` e `iig` para geração de interfaces
- Shims Linux para `xcrun`, `plutil` e `codesign`
- `lzfse` para processar o kernelcache

## Diagnóstico do erro no WSL

O instalador:

1. Procura `/opt/unixnu-linux/llvm/bin/clang`
2. Se já existe, não recompila o LLVM
3. Testa se o Clang possui `__builtin_xnu_type_summary` para `arm64e-apple-macos26.0`
4. Se o teste falhar, encerra a execução
5. Somente depois instala o shim `/usr/bin/xcrun`

Isso explica o erro:

```
unixnu: /usr/bin/xcrun missing; run "sudo scripts/linux/setup-toolchain.py /opt/unixnu-linux"
```

### Teste de validação do Clang

```bash
printf '#if __has_builtin(__builtin_xnu_type_summary)\nok\n#endif\n' |
/opt/unixnu-linux/llvm/bin/clang \
-target arm64e-apple-macos26.0 \
-E - | grep '^ok$'
```

Resultado esperado: `ok`

### Recuperação (se o Clang falhar na validação)

```bash
sudo mv /opt/unixnu-linux/llvm /opt/unixnu-linux/llvm.before-rebuild
sudo scripts/linux/setup-toolchain.py /opt/unixnu-linux
test -x /usr/bin/xcrun && echo "xcrun instalado"
/usr/bin/xcrun --version
```

## Issues relevantes no GitHub (UniXNU/UniXNU)

| Issue/PR | Status | Descrição |
|----------|--------|-----------|
| #182 | Aberta | Linux: kernel link fails on `__llvm_profile_*` — linker não encontra funções do runtime de profiling. Solução temporária: duas funções stub. |
| #183 | Aberta | Compile records survive OS profile switches — conflitos entre targets `arm64e-apple-ios17.0.0` vs `arm64e-apple-ios27.0`. Solução: `rm -rf out/<device>/<profile>/<config>/tree/build/xnu`. |
| #181 | Aberta | Derive the Linux toolchain target from selected profiles — corrige `linux_env()` para selecionar arquitetura e versão do SO corretamente. Não incorporado. |
| #184 | Aberta | Kernel prelink falha com `Native kernel lacks sparse-prelink index ABI` — o patch `kits/XnuPrelink/patches/xnu-10063.141.1-sparse-index.patch` não é aplicado automaticamente ao source do XNU. Solução: aplicar manualmente o patch em `tree/.cache/xnu-work/osfmk/kern/kalloc.c` (adiciona `__attribute__((used)) const uint32_t kalloc_sparse_prelink_index_version = 1;`) e reconstruir o kernel. |

## Avaliação para o port Hawaii

| Componente | Avaliação |
|------------|-----------|
| DTS e configuração | Pode continuar no WSL |
| Drivers C++ | Pode continuar no WSL |
| Toolchain XNU | Linux oficialmente suportado |
| Clang personalizado | Precisa passar na validação `__builtin_xnu_type_summary` |
| `xcrun` | Shim Linux, não exige Xcode instalado |
| Kernel ARM64e | Possível no Linux, com ajustes de target |
| Firmware EDK2 | Pode ser construído no Linux |
| Boot image | Pode ser construída no Linux |

**Recomendação:** não abandonar o build Linux nem migrar imediatamente para um Mac. Primeiro corrigir e validar a toolchain personalizada. Depois investigar a seleção do target macOS 26 no `kernel.py` e os problemas de link documentados na Issue #182.
