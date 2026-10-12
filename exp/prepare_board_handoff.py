#!/usr/bin/env python3
"""Archive a verified runtime SRCNN IP and its generated register map."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from reproduce_exp import archived
from route_gates import archive_route_evidence
from rtl_acceptance import accepted_cosim
from run_exp import ROOT, EXPERIMENT_ID, check_protected, markdown_table, number, utc, write_json
from verify_exp import check_image_validation

REMOTE = "/home/lipuze/amdprojects/90096_CNN_FPGA"


def validate_handoff(config, route, rtl_config, rtl_metrics):
    period = number(config.get("verification", {}).get("impl_target_clock_ns"))
    if config.get("operation") != "impl" or route.get("route_feasible") is not True or period is None or period <= 0:
        raise RuntimeError("Handoff requires independently closed, resource-feasible routing")
    parent = config.get("verify_parent")
    if not parent or rtl_config.get("verify_parent") != parent:
        raise RuntimeError("Implementation and cosimulation must use the same frozen parent")
    if config.get("parent_config", {}).get("top", "srcnn") != "srcnn":
        raise RuntimeError("This handoff requires the runtime-loaded srcnn interface")
    verification = rtl_config.get("verification", {})
    reload = rtl_config.get("reload_validation", {})
    if (not accepted_cosim(rtl_metrics, rtl_config) or not rtl_config.get("reload_params") or
            verification.get("changed_params_bit_exact") is not True or
            reload.get("frame_count") != 2 or reload.get("reload_pass") is not True or
            reload.get("bit_exact") is not True):
        raise RuntimeError("Handoff requires accepted, exact changed-parameter two-frame RTL")
    for key in ("rtl_latency_max", "rtl_interval_max"):
        value = number(verification.get(key))
        if value is None or value <= 0 or not value.is_integer():
            raise RuntimeError("Missing positive integer RTL cycle measurement: " + key)
    return parent, period


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("implementation", nargs="?", default="F98")
    parser.add_argument("--cosim")
    args = parser.parse_args()
    cosim_id = args.cosim or ("F97" if args.implementation == "F98" else None)
    if not cosim_id:
        parser.error("--cosim is required for a new implementation handoff")
    if any(not re.fullmatch(EXPERIMENT_ID, exp_id) for exp_id in (args.implementation, cosim_id)):
        parser.error("Expected an experiment ID")
    check_protected()
    archive = archived(args.implementation)
    config = json.loads((archive/"config.json").read_text())
    metrics = json.loads((archive/"metrics.json").read_text())
    rtl_archive = archived(cosim_id)
    rtl_config = json.loads((rtl_archive/"config.json").read_text())
    rtl_metrics = json.loads((rtl_archive/"metrics.json").read_text())
    verification = archive_route_evidence(archive)
    parent, period = validate_handoff(config, verification, rtl_config, rtl_metrics)
    if metrics.get("status") != "impl_complete":
        raise RuntimeError("Implementation did not complete")
    parent_config = json.loads((archived(parent)/"config.json").read_text())
    validation_config = json.loads((archived(config.get("validation_parent", parent))/"config.json").read_text())
    check_image_validation(parent_config, validation_config)
    check_image_validation(config["parent_config"], validation_config)
    check_image_validation(rtl_config["parent_config"], validation_config)
    rtl = rtl_config["verification"]
    remote_package = REMOTE + "/workspace/exp_runs/" + args.implementation + "/hls/impl/ip/xilinx_com_hls_srcnn_1_0.zip"
    scratch = ROOT/"workspace/exp_runs/_handoff"/args.implementation
    scratch.mkdir(parents=True, exist_ok=True)
    local = scratch/"xilinx_com_hls_srcnn_1_0.zip"
    ssh = ["ssh", "-F", str(ROOT.parent/"ssh-config"), "-o", "BatchMode=yes", "xiaoxin-ubuntu"]
    before = subprocess.check_output(ssh + ["sha256sum " + remote_package], text=True).split()[0]
    subprocess.run(["scp", "-F", str(ROOT.parent/"ssh-config"),
                    "xiaoxin-ubuntu:" + remote_package, str(local)], check=True)
    digest = hashlib.sha256(local.read_bytes()).hexdigest()
    after = subprocess.check_output(ssh + ["sha256sum " + remote_package], text=True).split()[0]
    if before != digest or after != digest:
        raise RuntimeError("IP package changed during collection")
    dest = ROOT/"experiments/board_handoff"/args.implementation
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
    record = {"time": utc(), "parent": parent, "implementation": args.implementation, "cosimulation": cosim_id,
              "source_commit": config["parent_metrics"]["git_commit"],
              "verification_commit": config["source_commit"], "tool_version": config["tool_version"],
              "remote_ip_package": remote_package, "local_ip_package": str(local.relative_to(ROOT)),
              "package_sha256": digest, "package_bytes": local.stat().st_size,
              "rtl_latency_cycles": cycles, "rtl_interval_cycles": rtl["rtl_interval_max"],
              "route_clock_ns": period, "max_ooc_clock_mhz": 1000/period,
              "ideal_ip_frame_ms": cycles*period/1e6, "route": verification,
              "precision": parent_config["precision"], "validation_parent": config.get("validation_parent", parent),
              "butterfly_reference": parent_config["reference"],
              "all_image_reference_directory": parent_config.get("numpy_reference"),
              "image_count": validation_config["validation"]["image_count"],
              "delta_psnr": validation_config["validation"]["delta_psnr"],
              "registers": registers, "drivers": records, "board_validation": "unknown"}
    write_json(dest/"manifest.json", record)
    legacy = args.implementation == "F98"
    prefix = "" if legacy else "../../"
    manifest_prefix = "board_handoff/F98/" if legacy else ""
    text = "# " + args.implementation + " board handoff\n\n"
    text += "Runtime-loaded candidate " + parent + ", independently implemented as [" + args.implementation + "](" + prefix + metrics["md_path"] + "). "
    text += "This is an out-of-context IP package; complete-system DDR/interconnect timing and board performance remain unmeasured. "
    text += "Retain the existing F98 handoff as an independently verified integration fallback.\n\n" if not legacy else "No ROM candidate replaces it.\n\n"
    text += "## Package and provenance\n\n"
    text += "Remote package: `" + remote_package + "`.\n\nLocal collected package: `" + str(local.relative_to(ROOT)) + "`. "
    text += "Generated RTL and the ZIP remain outside Git; only driver sources/registers and this manifest are archived.\n\n"
    text += "SHA256: `" + digest + "`.\n\n"
    text += "[Manifest](" + manifest_prefix + "manifest.json), [register header](" + manifest_prefix + "xsrcnn_hw.h).\n\n"
    text += markdown_table([{"metric": key, "value": record[key]} for key in
                            ("source_commit", "rtl_latency_cycles", "rtl_interval_cycles", "route_clock_ns",
                             "max_ooc_clock_mhz", "ideal_ip_frame_ms", "precision", "image_count", "delta_psnr",
                             "board_validation")], ["metric", "value"])
    text += "\nThe OOC clock above comes from an independently closed implementation. "
    text += "HLS packaging frequency metadata is not physical timing approval.\n"
    text += "\nButterfly bit comparison uses `" + record["butterfly_reference"] + "`. "
    text += "All-image references are in `" + str(record["all_image_reference_directory"]) + "`. "
    text += "Use this candidate's precision reference when checking output bits.\n"
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
    text += "1. Integrate this IP and independently close the complete block-design timing. " + args.implementation + "'s OOC clock limit is" + format(1000/period, ".6g") + "MHz.\n"
    text += "2. Read the actual PL clock registers; record frequency and divider rather than assuming the requested frequency. "
    text += "For a1000MHz IOPLL, select a supported divider giving a period no shorter than" + format(period, ".6g") + "ns.\n"
    text += "3. Use the same bitstream at two supported PL clocks. Record IP-start/done latency separately from allocations, "
    text += "cache maintenance, DDR and driver overhead. Convert measured elapsed time to PL cycles.\n"
    text += "4. Measure one invocation and repeated invocations, retaining runtime weight reload. Check all output bits "
    text += "against the fixed reference and the six-pixel border before accepting performance.\n"
    text += "5. Record actual board/bitstream/software commits, actual clocks, outputs and timing distributions here; "
    text += "no board measurement has been provided yet.\n"
    document = ROOT/"experiments/BOARD_HANDOFF.md" if legacy else dest/"HANDOFF.md"
    document.write_text(text)
    check_protected()
    print(json.dumps({key: record[key] for key in ("remote_ip_package", "package_sha256", "ideal_ip_frame_ms")}, indent=2))


if __name__ == "__main__":
    main()
