#!/usr/bin/env python3
import argparse, re, sys
from pathlib import Path

ERRORS = []
WARNINGS = []
INFO = []

def error(msg):
    ERRORS.append(msg); print("  ERROR: " + msg)

def warning(msg):
    WARNINGS.append(msg); print("  WARNING: " + msg)

def info(msg):
    INFO.append(msg); print("  INFO: " + msg)

def read_file(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        error("Cannot read " + str(path) + ": " + str(e))
        return ""

def check_node(dts_content, node_path, description):
    patterns = [node_path.split("/")[-1] + ":", "/" + node_path.strip("/"), "&" + node_path.split("/")[-1]]
    found = any(p in dts_content for p in patterns)
    if not found:
        error("Missing DTS node: " + node_path + " (" + description + ")")
    else:
        info("Found node: " + node_path)

def check_prop(dts_content, node, prop, expected=None):
    pattern = re.escape(node) + r"[^{]*?" + re.escape(prop) + r"s*="
    if re.search(pattern, dts_content, re.DOTALL):
        if expected is not None:
            prop_pattern = re.escape(prop) + r"s*=s*([^;}]+)"
            m = re.search(prop_pattern, dts_content)
            if m and expected in m.group(1):
                info("Property " + node + "." + prop + " matches expected")
            else:
                warning("Property " + node + "." + prop + " may not match expected: " + expected)
        info("Found property: " + node + "." + prop)
    else:
        error("Missing property: " + node + "." + prop)

def main():
    parser = argparse.ArgumentParser(description="Validate hawaii Device Tree")
    parser.add_argument("--dts", default="dts/hawaii.dts")
    parser.add_argument("--dtsi", default="soc/UniXNU-ums9230-common/dts/ums9230.dtsi")
    parser.add_argument("--components", default="components")
    args = parser.parse_args()

    print("=== Validating hawaii Device Tree ===
")

    dts_content = read_file(args.dts)
    dtsi_content = read_file(args.dtsi)

    if not dts_content and not dtsi_content:
        error("No DTS files to validate")
        return 1

    combined = dts_content + dtsi_content

    print("--- Required DTS Nodes ---")
    check_node(combined, "/memory@80000000", "Memory region")
    check_node(combined, "/reserved-memory", "Reserved memory")
    check_node(combined, "/soc", "SoC bus")
    check_node(combined, "/soc/gic", "GIC interrupt controller")
    check_node(combined, "/soc/timer", "ARM arch timer")
    check_node(combined, "/soc/sdhci", "SDHCI controller")
    check_node(combined, "/soc/gpu", "GPU (Mali-G57)")
    check_node(combined, "/soc/display-subsystem", "Display subsystem")
    check_node(combined, "/soc/touch", "Touch panel")
    check_node(combined, "/soc/power-controller", "PMIC SC2730")
    check_node(combined, "/cpus", "CPU complex")

    print("
--- DTS Properties ---")
    check_prop(combined, "interrupt-controller", "compatible", "arm,gic-v3")
    check_prop(combined, "timer", "compatible", "arm,armv8-timer")
    check_prop(combined, "gpu", "compatible", "sprd,mali-natt")
    check_prop(combined, "sdhci", "compatible", "unixnu,sdhci-block")

    print("
--- AGENTS.md Compliance ---")
    if "unixnu,cluster-type" in combined:
        error("AGENTS.md violation: unixnu,cluster-type found in DTS")
    else:
        info("OK: No unixnu,cluster-type in DTS")

    print("
--- Vendor DTB Verification ---")
    if "interrupt-controller@10000000" in combined:
        info("OK: GIC at correct address 0x10000000")
    elif "interrupt-controller@12000000" in combined:
        error("GIC at wrong address 0x12000000")
    else:
        error("GIC node not found")

    if "0x53f0000" in combined and "0xfabff000" in combined:
        info("OK: Memory regions match vendor DTB (4GiB carve-out)")
    else:
        error("Memory regions do not match vendor DTB")

    print("
--- Component TOMLs ---")
    components_dir = Path(args.components)
    if components_dir.exists():
        for toml_file in sorted(components_dir.glob("*/*.toml")):
            component_name = toml_file.parent.name
            driver_dir = Path("drivers") / component_name
            if driver_dir.exists():
                cpp_files = list(driver_dir.glob("*.cpp"))
                if cpp_files:
                    info("OK: " + str(toml_file) + " has matching driver in " + str(driver_dir))
                else:
                    warning(str(toml_file) + " has no matching .cpp in " + str(driver_dir))
            else:
                warning(str(toml_file) + " has no matching driver directory " + str(driver_dir))

    print("
" + "="*50)
    print("VALIDATION SUMMARY")
    print("="*50)
    print("Errors:   " + str(len(ERRORS)))
    print("Warnings: " + str(len(WARNINGS)))
    print("Info:     " + str(len(INFO)))

    if ERRORS:
        print("
FAILED: Fix errors before proceeding")
        return 1
    elif WARNINGS:
        print("
PASSED with warnings")
        return 0
    else:
        print("
PASSED: All checks passed")
        return 0

if __name__ == "__main__":
    sys.exit(main())
