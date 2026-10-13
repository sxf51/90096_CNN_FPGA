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
    top = config.get("parent_config", {}).get("top", "srcnn")
    if top not in {"srcnn", "srcnn_reload"}:
        raise RuntimeError("This handoff requires a verified runtime-parameter interface")
    verification = rtl_config.get("verification", {})
    reload = rtl_config.get("reload_validation", {})
    if not accepted_cosim(rtl_metrics, rtl_config):
        raise RuntimeError("Handoff requires accepted exact RTL verification")
    if top == "srcnn_reload":
        from monitored_cosim import measured_axi
        from reload_switch_evidence import check_c_sequence
        if (not rtl_config.get("reload_switch_validation") or
                verification.get("reload_switch_bit_exact") is not True or
                verification.get("skip_parameter_axi_zero") is not True or
                verification.get("rtl_frame_count") != 4):
            raise RuntimeError("Reload handoff requires four exact calls and zero skipped parameter AXI")
        check_c_sequence(verification.get("functional_validation", {}))
        transactions = verification.get("reload_switch_transactions", [])
        count_keys = ("transaction", "load_params", "ar_requests", "r_beats", "aw_requests", "w_beats",
                      "ar_valid_cycles", "r_valid_cycles", "aw_valid_cycles", "w_valid_cycles", "read_bytes")
        measured_axi([{key: item[key] for key in count_keys} for item in transactions])
    elif (not rtl_config.get("reload_params") or verification.get("changed_params_bit_exact") is not True or
          reload.get("frame_count") != 2 or reload.get("reload_pass") is not True or
          reload.get("bit_exact") is not True):
        raise RuntimeError("Handoff requires accepted, exact changed-parameter two-frame RTL")
    for key in ("rtl_latency_max", "rtl_interval_max"):
        value = number(verification.get(key))
        if value is None or value <= 0 or not value.is_integer():
            raise RuntimeError("Missing positive integer RTL cycle measurement: " + key)
    return parent, period


def register_map(header, top):
    prefix = top.upper()
    fields = re.findall(r"^#define X" + prefix + r"_CONTROL_ADDR_(\w+)_DATA\s+(0x[0-9a-f]+)$",
                        header, re.MULTILINE)
    expected = {"in_r", "out_r", "weights1", "biases1", "weights2", "biases2", "weights3", "biases3"}
    if top == "srcnn_reload":
        expected.add("load_params")
    if len(fields) != len(expected) or {name.lower() for name, _ in fields} != expected:
        raise RuntimeError("Unexpected runtime parameter register map")
    registers = []
    for name, offset in fields:
        scalar = name.lower() == "load_params"
        registers.append({"argument": name.lower(), "offset": offset,
                          "pointer_bits": None if scalar else 64})
        if scalar:
            width = re.findall(r"^#define X" + prefix + "_CONTROL_BITS_" + name + r"_DATA\s+(\d+)$",
                               header, re.MULTILINE)
            if width != ["1"]:
                raise RuntimeError("load_params must be the generated one-bit control argument")
            registers[-1]["scalar_bits"] = 1
    return registers


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
    top = parent_config.get("top", "srcnn")
    reload_switch = top == "srcnn_reload"
    validation_config = json.loads((archived(config.get("validation_parent", parent))/"config.json").read_text())
    check_image_validation(parent_config, validation_config)
    check_image_validation(config["parent_config"], validation_config)
    check_image_validation(rtl_config["parent_config"], validation_config)
    rtl = rtl_config["verification"]
    package_name = "xilinx_com_hls_" + top + "_1_0.zip"
    remote_package = REMOTE + "/workspace/exp_runs/" + args.implementation + "/hls/impl/ip/" + package_name
    scratch = ROOT/"workspace/exp_runs/_handoff"/args.implementation
    scratch.mkdir(parents=True, exist_ok=True)
    local = scratch / package_name
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
        if [fields[key] for key in ("vendor", "library", "name", "version")] != ["xilinx.com", "hls", top, "1.0"]:
            raise RuntimeError("Unexpected IP VLNV")
        drivers = [name for name in package.namelist()
                   if name.startswith("drivers/" + top + "_v1_0/src/") and name.endswith((".h", ".c"))]
        if not any(name.endswith("x" + top + "_hw.h") for name in drivers):
            raise RuntimeError("No generated register map in IP")
        records = []
        for name in drivers:
            data = package.read(name)
            (dest/Path(name).name).write_bytes(data)
            records.append({"file": Path(name).name, "zip_member": name,
                            "sha256": hashlib.sha256(data).hexdigest()})
    header_name = "x" + top + "_hw.h"
    registers = register_map((dest / header_name).read_text(), top)
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
    if reload_switch:
        record["reload_transactions"] = [dict(item, ideal_ip_frame_ms=item["latency_cycles"] * period / 1e6)
                                         for item in rtl["reload_switch_transactions"]]
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
    text += "[Manifest](" + manifest_prefix + "manifest.json), [register header](" + manifest_prefix + header_name + ").\n\n"
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
    text += ("The srcnn_reload float32 signature adds one load_params control bit and exports image_in and image_out m_axi bundles, "
             if reload_switch else "The unchanged srcnn float32 signature exports image_in and image_out m_axi bundles, ")
    text += "one shared parameters m_axi bundle, and control s_axilite. Images contain65025 row-major floats "
    text += "(260100bytes). Weights follow Cout/Cin/kernel-row/kernel-column: Conv1=5184, Conv2=2048, "
    text += "Conv3=800 floats, and biases=64/32/1 floats. "
    text += ("Parameters load when load_params=1; a fresh IP also forces loading on its first call when load_params=0. "
             if reload_switch else "Parameters load on every invocation. ")
    text += "The generated control pointers are64-bit; offsets below are their low words and the high word is offset+4.\n\n"
    text += markdown_table(registers, ["argument", "offset", "pointer_bits"] + (["scalar_bits"] if reload_switch else []))
    if reload_switch:
        text += ("\nSet load_params=1 on the first frame after loading/resetting the IP and whenever weights change; "
                 "set it to0 for subsequent frames using the most recently loaded banks. Incoming parameter pointers "
                 "are ignored on reused calls; keep valid parameter buffers available for the cold-start fallback. "
                 "Use the generated driver setter, not a hardcoded offset. The original srcnn C wrapper always loads.\n\n")
        text += markdown_table(record["reload_transactions"],
                               ["transaction", "load_params", "latency_cycles", "interval_cycles", "read_bytes",
                                "ar_valid_cycles", "r_valid_cycles", "ideal_ip_frame_ms"])
        text += "\nThese four separate IP times describe initial load, reuse, reload and retained-latest calls; continuous video uses the normal-weight reuse transaction.\n"
    text += "\nAP control=0x00; start bit0, done bit1(clear-on-read), idle bit2, ready bit3 and auto_restart bit7. "
    text += "Use the generated driver as the authoritative interface. Flush input/parameter caches before starting "
    text += "and invalidate output caches after completion when using cacheable host buffers.\n\n"
    text += "## Board measurements\n\n"
    text += "1. Integrate this IP and independently close the complete block-design timing. " + args.implementation + "'s OOC clock limit is" + format(1000/period, ".6g") + "MHz.\n"
    text += "2. Read the actual PL clock registers; record frequency and divider rather than assuming the requested frequency. "
    text += "For a1000MHz IOPLL, select a supported divider giving a period no shorter than" + format(period, ".6g") + "ns.\n"
    text += "3. Use the same bitstream at two supported PL clocks. Record IP-start/done latency separately from allocations, "
    text += "cache maintenance, DDR and driver overhead. Convert measured elapsed time to PL cycles.\n"
    text += ("4. Measure the first loaded frame and subsequent reused frames separately; verify a later load=1 weight update. Check all output bits "
             if reload_switch else "4. Measure one invocation and repeated invocations, retaining runtime weight reload. Check all output bits ")
    text += "against the fixed reference and the six-pixel border before accepting performance.\n"
    text += "5. Record actual board/bitstream/software commits, actual clocks, outputs and timing distributions here; "
    text += "no board measurement has been provided yet.\n"
    document = ROOT/"experiments/BOARD_HANDOFF.md" if legacy else dest/"HANDOFF.md"
    document.write_text(text)
    check_protected()
    print(json.dumps({key: record[key] for key in ("remote_ip_package", "package_sha256", "ideal_ip_frame_ms")}, indent=2))


if __name__ == "__main__":
    main()
