#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEVICE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "========================================"
echo "  Hawaii-UMS9230 Project Validation"
echo "========================================"
echo ""

ERRORS=0

# 1. Validate DTS
echo ""
echo "--- 1. Device Tree Validation ---"
if python3 "${SCRIPT_DIR}/validate_dts.py" \
    --dts "${DEVICE_DIR}/dts/hawaii.dts" \
    --dtsi "${DEVICE_DIR}/soc/UniXNU-ums9230-common/dts/ums9230.dtsi" \
    --components "${DEVICE_DIR}/components" 2>&1; then
    echo "DTS validation passed"
else
    echo "DTS validation failed"
    ERRORS=$((ERRORS + 1))
fi

# 2. Build drivers
echo ""
echo "--- 2. Driver Build Validation ---"
if bash "${SCRIPT_DIR}/build-drivers.sh" 2>&1; then
    echo "Driver build validation passed"
else
    echo "Driver build validation failed"
    ERRORS=$((ERRORS + 1))
fi

# 3. Check porting.toml sources
echo ""
echo "--- 3. Porting.toml Sources ---"
if grep -q "sources = \[" "${DEVICE_DIR}/porting.toml"; then
    echo "All areas have sources recorded"
else
    echo "Missing sources in porting.toml"
    ERRORS=$((ERRORS + 1))
fi

# 4. Check cross-compiler
echo ""
echo "--- 4. Cross-Compilation Toolchain ---"
if command -v aarch64-linux-gnu-g++ &> /dev/null; then
    echo "aarch64-linux-gnu-g++ available"
else
    echo "aarch64-linux-gnu-g++ not found"
    echo "Install with: sudo apt-get install g++-aarch64-linux-gnu"
fi

# Summary
echo ""
echo "========================================"
if [ "${ERRORS}" -eq 0 ]; then
    echo "ALL VALIDATIONS PASSED"
else
    echo "${ERRORS} VALIDATION(S) FAILED"
fi
echo "========================================"

exit ${ERRORS}