"""Use HLS setup and its generated simulation driver with a read-only AXI observer."""
import csv
import hashlib
import re
import shutil
from run_exp import ROOT, write_json
from reload_switch_evidence import check_rtl_metrics, parse_transactions


def install_monitor(work, archive):
    simulation = work / "hls/sim/verilog"
    testbench = simulation / "srcnn_reload.autotb.v"
    original = testbench.read_text()
    count = re.findall(r"parameter AUTOTB_TRANSACTION_NUM = (\d+);", original)
    if count != ["4"] or original.count("endmodule") != 1 or "exp_axi_transaction" in original:
        raise RuntimeError("Need a fresh four-transaction HLS simulation harness")
    required = ("AESL_start", "AESL_start_p1", "AESL_ready_p1", "AESL_done", "ap_clk", "ap_rst_n",
                "parameters_ARVALID", "parameters_ARREADY", "parameters_ARLEN", "parameters_ARSIZE",
                "parameters_RVALID", "parameters_RREADY", "parameters_AWVALID", "parameters_AWREADY",
                "parameters_WVALID", "parameters_WREADY")
    if any(not re.search(r"\b" + name + r"\b", original) for name in required):
        raise RuntimeError("Generated simulation harness lacks required AXI/control observations")
    template = ROOT / "exp/tb/parameter_axi_monitor.vh"
    monitor = template.read_text()
    patched = original.replace("endmodule", monitor + "\nendmodule", 1)
    folder = archive / "parameter_axi_monitor"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "parameter_axi_monitor.vh").write_text(monitor)
    testbench.write_text(patched)
    record = {"raw_testbench": str(testbench.relative_to(work)),
              "original_sha256": hashlib.sha256(original.encode()).hexdigest(),
              "instrumented_sha256": hashlib.sha256(patched.encode()).hexdigest(),
              "observer_sha256": hashlib.sha256(monitor.encode()).hexdigest(),
              "scope": "Read-only AXI observer in generated simulation testbench; synthesis RTL unchanged"}
    write_json(folder / "manifest.json", record)
    return record


def run_monitored(config, work, archive, timeout, invoke_phase):
    setup = work / "cosim_setup_config.cfg"
    setup.write_text((work / "hls_config.cfg").read_text() + "cosim.setup=true\n")
    shutil.copyfile(setup, archive / setup.name)
    code, first_seconds = invoke_phase(
        ["vitis-run", "--mode", "hls", "--cosim", "--config", str(setup), "--work_dir", str(work)],
        ROOT, work / "cosim_setup.console.log", timeout, "cosim_setup")
    if code:
        shutil.copyfile(work / "cosim_setup.console.log", work / "cosim.console.log")
        return code, first_seconds
    config["parameter_axi_monitor"] = install_monitor(work, archive)
    driver = work / "cosim_execute.tcl"
    # The generated driver retains vector checks, dataflow profiling and RTL post-checking.
    driver.write_text("cd {" + (work / "hls/sim/verilog").as_posix() + "}\n"
                      "source run_sim.tcl\nputs EXP_MONITORED_COSIM_DONE\nexit\n")
    shutil.copyfile(driver, archive / driver.name)
    remaining = timeout - first_seconds
    if remaining <= 0:
        return 124, first_seconds
    code, second_seconds = invoke_phase(
        ["vitis-run", "--mode", "hls", "--tcl", str(driver), "--work_dir", str(work)],
        ROOT, work / "cosim_execute.console.log", remaining, "cosim_execute")
    target = work / "cosim.console.log"
    with target.open("wb") as output:
        for path in (work / "cosim_setup.console.log", work / "cosim_execute.console.log"):
            with path.open("rb") as source:
                shutil.copyfileobj(source, output)
    return code, first_seconds + second_seconds


def measured_axi(rows):
    expected = [1, 0, 1, 0]
    fields = ("ar_requests", "r_beats", "aw_requests", "w_beats", "ar_valid_cycles",
              "r_valid_cycles", "aw_valid_cycles", "w_valid_cycles", "read_bytes")
    if len(rows) != 4 or [int(row["transaction"]) for row in rows] != list(range(4)):
        raise RuntimeError("Missing or duplicated parameter AXI transaction observations")
    for row, load in zip(rows, expected):
        if int(row["load_params"]) != load or any(int(row[field]) < 0 for field in fields):
            raise RuntimeError("Wrong load control or negative AXI count")
        if any(int(row[field]) for field in ("aw_requests", "w_beats", "aw_valid_cycles", "w_valid_cycles")):
            raise RuntimeError("Unexpected parameter AXI writes")
        if load:
            if any(int(row[field]) <= 0 for field in ("ar_requests", "r_beats", "read_bytes")):
                raise RuntimeError("Loaded transaction has no observed parameter AXI reads")
        elif any(int(row[field]) for field in fields):
            raise RuntimeError("Skipped-load transaction has parameter AXI traffic")
    return [{key: int(value) for key, value in row.items()} for row in rows]


def measured_result(work, archive, parent):
    text = (work / "cosim.console.log").read_text(errors="replace")
    if "EXP_MONITORED_COSIM_DONE" not in text:
        raise RuntimeError("Generated simulation and post-check driver did not complete")
    functional = check_rtl_metrics(text, parent)
    performance = work / "hls/sim/verilog/srcnn_reload.performance.result.transaction.xml"
    transactions = parse_transactions(performance.read_text())
    bus = work / "hls/sim/verilog/reload_parameter_axi.csv"
    with bus.open(newline="") as stream:
        observed = measured_axi(list(csv.DictReader(stream)))
    for index, row in enumerate(transactions):
        row.update(observed[index])
        row["parameter_axi_zero"] = row["load_params"] == 0 and row["read_bytes"] == 0
    from analyze_arch import write_csv
    write_csv(archive / "reload_transactions.csv", transactions, list(transactions[0]))
    folder = archive / "parameter_axi_monitor"
    for source in (performance, bus):
        shutil.copyfile(source, folder / source.name)
    report_manifest = {source.name: {"raw_file": str(source.relative_to(work)),
                                    "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
                       for source in (performance, bus)}
    write_json(folder / "measurement_manifest.json", report_manifest)
    latencies = [row["latency_cycles"] for row in transactions]
    intervals = [row["interval_cycles"] for row in transactions if row["interval_cycles"] is not None]
    return {"rtl_status": "Pass", "rtl_latency_min": min(latencies),
            "rtl_latency_avg": sum(latencies) / len(latencies), "rtl_latency_max": max(latencies),
            "rtl_interval_min": min(intervals), "rtl_interval_avg": sum(intervals) / len(intervals),
            "rtl_interval_max": max(intervals), "reload_switch_transactions": transactions,
            "reload_switch_bit_exact": True, "skip_parameter_axi_zero": True,
            "rtl_frame_count": 4, "functional_validation": functional,
            "measurement_backend": "HLS-generated simulation/post-check with read-only AXI observer"}
