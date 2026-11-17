#!/bin/bash
set -e

echo "=== Montando unidade D ==="
sudo mkdir -p /mnt/d 2>/dev/null || true
sudo mount -t drvfs D: /mnt/d 2>/dev/null || true

# Verificar se montou
if [ -d /mnt/d ]; then
    echo "✓ Unidade D montada em /mnt/d"
else
    echo "✗ Não foi possível montar /mnt/d"
    exit 1
fi

# Verificar se o diretório do projeto existe
if [ -d /mnt/d/GitHub/hawaii-unixnu ]; then
    echo "✓ Diretório hawaii-unixnu encontrado"
else
    echo "✗ Diretório hawaii-unixnu não encontrado em /mnt/d/GitHub/"
    exit 1
fi

# Verificar se o unixnu-core existe
if [ -d /mnt/d/GitHub/unixnu-core ]; then
    echo "✓ Diretório unixnu-core encontrado"
else
    echo "✗ Diretório unixnu-core não encontrado"
    exit 1
fi

# Verificar python3
if command -v python3 &> /dev/null; then
    echo "✓ Python3 encontrado: $(python3 --version)"
else
    echo "✗ Python3 não encontrado"
    exit 1
fi

# Verificar se o unixnu funciona
echo "Testando unixnu..."
cd /mnt/d/GitHub/unixnu-core
python3 unixnu --help 2>&1 | head -5

echo ""
echo "=== Ambiente pronto para build ==="
echo "Para configurar o hawaii:"
echo "  cd /mnt/d/GitHub/unixnu-core"
echo "  python3 unixnu defconfig hawaii -D /mnt/d/GitHub/hawaii-unixnu"
echo ""
echo "Para fazer o build:"
echo "  python3 unixnu build -D /mnt/d/GitHub/hawaii-unixnu"
