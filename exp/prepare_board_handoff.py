#!/usr/bin/env python3
"""Archive F98 IP provenance and its generated software register map."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from reproduce_exp import archived
from run_exp import ROOT, markdown_table, utc, write_json

REMOTE = "/home/lipuze/amdprojects/90096_CNN_FPGA"
PACKAGE = REMOTE + "/workspace/exp_runs/F98/hls/impl/ip/xilinx_com_hls_srcnn_1_0.zip"


def main():
    archive = archived("F98")
    config = json.loads((archive/"config.json").read_text())
    verification = config["verification"]
    rtl = json.loads((archived("F97")/"verification.json").read_text())
    if config.get("verify_parent") != "W21" or rtl.get("rtl_status") != "Pass":
        raise RuntimeError("Unexpected handoff provenance")
    if verification["impl_target_clock_ns"] != 5 or verification["impl_WNS_ns"] < 0:
        raise RuntimeError("The handoff must be the independently closed5ns F98 package")
    scratch = ROOT/"workspace/exp_runs/_handoff/F98"
    scratch.mkdir(parents=True, exist_ok=True)
    local = scratch/"xilinx_com_hls_srcnn_1_0.zip"
    ssh = ["ssh", "-F", str(ROOT.parent/"ssh-config"), "-o", "BatchMode=yes", "xiaoxin-ubuntu"]
    before = subprocess.check_output(ssh + ["sha256sum " + PACKAGE], text=True).split()[0]
    subprocess.run(["scp", "-F", str(ROOT.parent/"ssh-config"),
                    "xiaoxin-ubuntu:" + PACKAGE, str(local)], check=True)
    digest = hashlib.sha256(local.read_bytes()).hexdigest()
    after = subprocess.check_output(ssh + ["sha256sum " + PACKAGE], text=True).split()[0]
    if before != digest or after != digest:
        raise RuntimeError("IP package changed during collection")
    dest = ROOT/"experiments/board_handoff/F98"
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(local) as package:
        component = ET.fromstring(package.read("component.xml"))
        fields = {node.tag.rsplit("}", 1)[-1]: node.text for node in component}
        if [fields[key] for key in ("vendor", "library", "name", "version")] != ["xilinx.com", "hls", "srcnn", "1.0"]:
            raise RuntimeError("Unexpected IP VLNV")
        drivers = [name for name in package.namelist()
                   if name.startswith("drivers/srcnn_v1_0/src/") and name.endswith((".h", ".c"))]
        if not any(name.endswith("xsrcnn_hw.h") for name in drivers):
            raise RuntimeError("No generated register map in IP")
        records = []
        for name in drivers:
            data = package.read(name)
            (dest/Path(name).name).write_bytes(data)
            records.append({"file": Path(name).name, "zip_member": name,
                            "sha256": hashlib.sha256(data).hexdigest()})
    header = (dest/"xsrcnn_hw.h").read_text()
    registers = [{"argument": name.lower(), "offset": offset, "pointer_bits": 64}
                 for name, offset in re.findall(r"^#define XSRCNN_CONTROL_ADDR_(\w+)_DATA\s+(0x[0-9a-f]+)$",
                                                header, re.MULTILINE)]
    if len(registers) != 8:
        raise RuntimeError("Unexpected runtime-loaded srcnn pointer map")
    cycles = rtl["rtl_latency_max"]
    period = verification["impl_target_clock_ns"]
    record = {"time": utc(), "parent": "W21", "implementation": "F98", "cosimulation": "F97",
              "source_commit": config["parent_metrics"]["git_commit"],
              "verification_commit": config["source_commit"], "tool_version": config["tool_version"],
              "remote_ip_package": PACKAGE, "local_ip_package": str(local.relative_to(ROOT)),
              "package_sha256": digest, "package_bytes": local.stat().st_size,
              "rtl_latency_cycles": cycles, "rtl_interval_cycles": rtl["rtl_interval_max"],
              "route_clock_ns": period, "max_ooc_clock_mhz": 1000/period,
              "ideal_ip_frame_ms": cycles*period/1e6, "route": verification,
              "registers": registers, "drivers": records, "board_validation": "unknown"}
    write_json(dest/"manifest.json", record)
    text = "# F98 board handoff\n\n"
    text += "Runtime-loaded mainline W21, independently implemented as [F98](F98_ws_impl_W21/F98.md). "
    text += "This is an out-of-context IP package; complete-system DDR/interconnect timing and board performance remain unmeasured. "
    text += "No ROM candidate replaces it.\n\n"
    text += "## Package and provenance\n\n"
    text += "Remote package: `" + PACKAGE + "`.\n\nLocal collected package: `" + str(local.relative_to(ROOT)) + "`. "
    text += "Generated RTL and the ZIP remain outside Git; only driver sources/registers and this manifest are archived.\n\n"
    text += "SHA256: `" + digest + "`.\n\n"
    text += "[Manifest](board_handoff/F98/manifest.json), [register header](board_handoff/F98/xsrcnn_hw.h).\n\n"
    text += markdown_table([{"metric": key, "value": record[key]} for key in
                            ("source_commit", "rtl_latency_cycles", "rtl_interval_cycles", "route_clock_ns",
                             "max_ooc_clock_mhz", "ideal_ip_frame_ms", "board_validation")], ["metric", "value"])
    text += "\n## Interface\n\n"
    text += "The unchanged srcnn float32 signature exports image_in and image_out m_axi bundles, "
    text += "one shared parameters m_axi bundle, and control s_axilite. Images contain65025 row-major floats "
    text += "(260100bytes). Weights follow Cout/Cin/kernel-row/kernel-column: Conv1=5184, Conv2=2048, "
    text += "Conv3=800 floats, and biases=64/32/1 floats. Parameters load on every invocation. "
    text += "The generated control pointers are64-bit; offsets below are their low words and the high word is offset+4.\n\n"
    text += markdown_table(registers, ["argument", "offset", "pointer_bits"])
    text += "\nAP control=0x00; start bit0, done bit1(clear-on-read), idle bit2, ready bit3 and auto_restart bit7. "
    text += "Use the generated driver as the authoritative interface. Flush input/parameter caches before starting "
    text += "and invalidate output caches after completion when using cacheable host buffers.\n\n"
    text += "## Board measurements\n\n"
    text += "1. Integrate this IP and independently close the complete block-design timing. F98's OOC clock limit is200MHz.\n"
    text += "2. Read the actual PL clock registers; record frequency and divider rather than assuming the requested frequency. "
    text += "With a1000MHz IOPLL, divide5 gives200MHz.\n"
    text += "3. Use the same bitstream at two supported PL clocks. Record IP-start/done latency separately from allocations, "
    text += "cache maintenance, DDR and driver overhead. Convert measured elapsed time to PL cycles.\n"
    text += "4. Measure one invocation and repeated invocations, retaining runtime weight reload. Check all output bits "
    text += "against the fixed reference and the six-pixel border before accepting performance.\n"
    text += "5. Record actual board/bitstream/software commits, actual clocks, outputs and timing distributions here; "
    text += "no board measurement has been provided yet.\n"
    (ROOT/"experiments/BOARD_HANDOFF.md").write_text(text)
    print(json.dumps({key: record[key] for key in ("remote_ip_package", "package_sha256", "ideal_ip_frame_ms")}, indent=2))


if __name__ == "__main__":
    main()
