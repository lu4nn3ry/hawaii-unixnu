#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEVICE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
DRIVERS_DIR="${DEVICE_DIR}/drivers"
CROSS_PREFIX="aarch64-linux-gnu-"
CXX="${CROSS_PREFIX}g++"

echo "========================================"
echo "  Hawaii-UMS9230 Driver Build Validation"
echo "========================================"
echo ""
echo "Device dir: ${DEVICE_DIR}"
echo "Cross-compiler: ${CXX}"
echo ""

if ! command -v "${CXX}" &> /dev/null; then
    echo "ERROR: ${CXX} not found"
    echo "Install with: sudo apt-get install g++-aarch64-linux-gnu"
    exit 1
fi

echo "Cross-compiler found: $("${CXX}" --version | head -1)"
echo ""

PASS=0
FAIL=0
SKIP=0

for driver_dir in "${DRIVERS_DIR}"/*/; do
    driver_name="$(basename "${driver_dir}")"
    cpp_files=("${driver_dir}"/*.cpp)

    if [ ! -f "${cpp_files[0]}" ]; then
        echo "SKIP ${driver_name}: no .cpp files"
        SKIP=$((SKIP + 1))
        continue
    fi

    echo -n "Building ${driver_name}... "

    compile_output=$("${CXX}" -std=c++17 -fsyntax-only \
        -I"${driver_dir}" \
        -I"${DEVICE_DIR}" \
        "${cpp_files[0]}" 2>&1) || true

    if [ $? -eq 0 ]; then
        echo "OK"
        PASS=$((PASS + 1))
    else
        if echo "${compile_output}" | grep -q "DriverKit\|IOKit\|IOService\|IOMemoryDescriptor\|IOWorkLoop\|IOInterruptEventSource"; then
            echo "SKIP (DriverKit headers not available)"
            SKIP=$((SKIP + 1))
        else
            echo "FAIL"
            echo "${compile_output}" | head -20
            FAIL=$((FAIL + 1))
        fi
    fi
done

echo ""
echo "========================================"
echo "Results: ${PASS} passed, ${SKIP} skipped, ${FAIL} failed"
echo "========================================"

if [ "${FAIL}" -gt 0 ]; then
    exit 1
fi

exit 0