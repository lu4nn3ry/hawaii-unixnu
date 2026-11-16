#!/bin/bash
# Device packaging script for hawaii (Moto E32 / UMS9230).
# Produces the same two artifacts from a clean checkout with no edit.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "I: hawaii package script"
echo "I: device    = hawaii"
echo "I: soc       = UMS9230 (ums9230)"
echo "I: os_profile = ipados-17.7.11-21H461"
echo "I: bootimg   = header v2, pagesize 2048, kernel_offset 0x8000"
echo "I: nothing to package yet - bring-up skeleton"
