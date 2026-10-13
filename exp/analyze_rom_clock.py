#!/usr/bin/env python3
"""Derive docs/0005 comparisons without rewriting historical result statuses."""
import csv
import json
from analyze_arch import dsp_composition, write_csv
from host_memory import swap_summary
from run_exp import ROOT, number
from route_gates import archive_route_evidence
from rtl_acceptance import accepted_cosim, acceptance_basis

CONTROL_STAGES = {"rom_clock_ws0", "rom_clock_wsB_equivalence", "rom_clock_wsB_banks"}


def load(exp_id):
    paths = list((ROOT/"experiments").glob(exp_id + "_*/metrics.json"))
    if not paths:
        return None
    if len(paths) != 1:
        raise RuntimeError("Conflicting archive identity: " + exp_id)
    archive = paths[0].parent
    return archive, json.loads(paths[0].read_text()), json.loads((archive/"config.json").read_text())


def rtl_excess(hls_cycles, rtl_cycles):
    hls, rtl = number(hls_cycles), number(rtl_cycles)
    if hls is None or rtl is None:
        return {"rtl_hls_excess_cycles": None, "rtl_hls_excess_pct": None,
                "rtl_2pct_limit_cycles": None, "rtl_within_2pct": None}
    if hls <= 0 or rtl <= 0 or not hls.is_integer() or not rtl.is_integer():
        raise ValueError("Latency comparisons require positive integer cycle measurements")
    limit = int(hls)*102//100
    return {"rtl_hls_excess_cycles": int(rtl)-int(hls),
            "rtl_hls_excess_pct": 100*(rtl/hls-1),
            "rtl_2pct_limit_cycles": limit, "rtl_within_2pct": int(rtl) <= limit}


def reload_transactions(records, comparisons):
    from monitored_cosim import measured_axi
    count_keys = ("ar_requests", "r_beats", "aw_requests", "w_beats", "ar_valid_cycles",
                  "r_valid_cycles", "aw_valid_cycles", "w_valid_cycles", "read_bytes")
    result = []
    for _, row, config in records:
        if not config.get("reload_switch_validation") or not accepted_cosim(row, config):
            continue
        measured = config.get("verification", {})
        if (measured.get("reload_switch_bit_exact") is not True or
                measured.get("skip_parameter_axi_zero") is not True):
            raise RuntimeError("Accepted reload switch lacks exact/zero-AXI evidence")
        transactions = measured.get("reload_switch_transactions", [])
        if (len(transactions) != 4 or [item["transaction"] for item in transactions] != list(range(4)) or
                [item["load_params"] for item in transactions] != [1, 0, 1, 0]):
            raise RuntimeError("Accepted reload switch lacks four ordered measurements")
        measured_axi([{key: item[key] for key in ("transaction", "load_params", *count_keys)}
                      for item in transactions])
        routes = [candidate for candidate in comparisons if candidate["operation"] == "impl" and
                  candidate["parent"] == config["verify_parent"] and
                  candidate["route_feasible"] is True and candidate["rtl_source"] == row["id"]]
        for route in routes or [None]:
            clock = number(route["route_clock_ns"]) if route else None
            if route and (clock is None or clock <= 0):
                raise RuntimeError("Closed reload route lacks a positive clock")
            for item, case in zip(transactions, ("first_load", "reuse", "reload", "retain")):
                result.append({"id": route["id"] if route else row["id"],
                               "parent": config["verify_parent"], "rtl_source": row["id"],
                               "implementation_id": route["id"] if route else None,
                               "transaction": item["transaction"], "case": case,
                               "load_params": item["load_params"],
                               "latency_cycles": item["latency_cycles"],
                               "interval_cycles": item["interval_cycles"],
                               **{key: item[key] for key in count_keys},
                               "route_clock_ns": clock,
                               "ip_frame_ms": item["latency_cycles"] * clock / 1e6 if clock else None,
                               "md_path": route["md_path"] if route else row["md_path"],
                               "rtl_md_path": row["md_path"]})
    return result


def add_frame_timings(comparisons, transactions):
    for row in comparisons:
        row.update(first_load_frame_ms=None, steady_state_frame_ms=None,
                   ranking_frame_ms=None, ranking_basis=None)
        if row.get("route_feasible") is not True:
            continue
        row["ranking_frame_ms"] = number(row.get("rtl_frame_ms"))
        if row["ranking_frame_ms"] is not None:
            row["ranking_basis"] = "maximum_rtl_transaction"
        calls = [call for call in transactions if call.get("implementation_id") == row["id"]]
        if not calls:
            continue
        if (len(calls) != 4 or [call["case"] for call in calls] !=
                ["first_load", "reuse", "reload", "retain"] or
                any(call["parent"] != row["parent"] or call["rtl_source"] != row["rtl_source"] or
                    number(call["route_clock_ns"]) != number(row["route_clock_ns"]) or
                    number(call["ip_frame_ms"]) is None or number(call["ip_frame_ms"]) <= 0
                    for call in calls)):
            raise RuntimeError("Reuse ranking requires four matching verified calls and routed clock")
        row["first_load_frame_ms"] = number(calls[0]["ip_frame_ms"])
        row["steady_state_frame_ms"] = max(number(call["ip_frame_ms"]) for call in calls
                                           if call["case"] in {"reuse", "retain"})
        row["ranking_frame_ms"] = row["steady_state_frame_ms"]
        row["ranking_basis"] = "maximum_verified_reuse"


def main():
    state = json.loads((ROOT/"experiments/rom_clock_state.json").read_text())
    records = [item for exp_id in dict.fromkeys(["W21", "F97", "F98", "W22"] + state["experiment_ids"])
               if (item := load(exp_id)) is not None]
    rtl_by_parent = {}
    for archive, row, config in records:
        measured = number(config.get("verification", {}).get("rtl_latency_max"))
        if accepted_cosim(row, config) and measured is not None:
            rtl_by_parent.setdefault(config["verify_parent"], []).append((row["id"], measured))
    configs = {row["id"]: config for _, row, config in records}
    comparisons, estimates, composition, fifos, memory = [], [], [], [], []
    for archive, row, config in records:
        operation = config.get("operation", "csim" if config.get("csim_only") else "csim/csynth")
        parent = config.get("verify_parent", config.get("control_experiment"))
        physical = config.get("verification", {})
        route = archive_route_evidence(archive) if operation == "impl" else {}
        baseline = row["id"] in {"W21", "F97", "F98", "W22"}
        if baseline or config.get("stage") not in CONTROL_STAGES:
            record = {"id": row["id"], "series": row["series"], "parent": parent,
                      "operation": operation, "status": row["status"], "md_path": row["md_path"],
                      "precision": row["precision_w_a_acc"], "T": row["T_target"],
                      "HLS_cycles": number(row["latency_cycles"]), "HLS_interval": number(row["interval_cycles"]),
                      "HLS_clock_target_ns": number(row["clock_target_ns"]),
                      "HLS_clock_est_ns": number(row["clock_est_ns"]),
                      "HLS_latency_ms_est": number(row["latency_ms_est"]),
                      **{"HLS_"+key: number(row[key]) for key in ("DSP", "BRAM18K", "URAM", "LUT", "FF")},
                      "hls_screen_pass": config.get("hls_screen_pass"), "ii_ok": row.get("ii_ok"),
                      "bit_exact": row.get("bit_exact"), "border_mse": number(row["border_mse"]),
                      "image_count": config.get("validation", {}).get("image_count"),
                      "delta_psnr": number(row["delta_psnr"]),
                      "rtl_cycles": number(physical.get("rtl_latency_max")), "rtl_source": None,
                      "rtl_accepted": accepted_cosim(row, config) if operation == "cosim" else None,
                      "rtl_acceptance_basis": acceptance_basis(row, config) if operation == "cosim" else None,
                      "route_feasible": route.get("route_feasible"),
                      "route_clock_ns": number(physical.get("impl_target_clock_ns")),
                      "route_WNS_ns": route.get("impl_WNS_ns"), "route_WHS_ns": route.get("impl_WHS_ns"),
                      **{"route_"+key: route.get("impl_"+key) for key in ("DSP", "BRAM18K", "URAM", "LUT", "FF")},
                      "rtl_frame_ms": None, "notes": row.get("notes", "")}
            matching_parent = parent if operation == "impl" else row["id"]
            if operation != "cosim" and len(rtl_by_parent.get(matching_parent, [])) == 1:
                record["rtl_source"], record["rtl_cycles"] = rtl_by_parent[matching_parent][0]
                if record["route_feasible"] is True and record["route_clock_ns"] is not None:
                    record["rtl_frame_ms"] = record["rtl_cycles"]*record["route_clock_ns"]/1e6
            accepted_rtl = record["rtl_cycles"] if record["rtl_source"] or accepted_cosim(row, config) else None
            record.update(rtl_excess(record["HLS_cycles"], accepted_rtl))
            stage = config.get("stage", "") if operation != "cosim" else configs.get(parent, {}).get("stage", "")
            record["wsD_goal_met"] = record["rtl_within_2pct"] if str(stage).startswith("rom_clock_wsD") else None
            comparisons.append(record)
        if not baseline and config.get("stage") not in CONTROL_STAGES:
            paper = config.get("estimates", {})
            for key in ("DSP", "BRAM18K", "URAM", "LUT", "FF", "latency_cycles"):
                expected = number(paper.get(key))
                if operation == "cosim":
                    actual = number(physical.get("rtl_latency_max")) if key == "latency_cycles" else None
                    domain = "RTL"
                elif operation == "impl":
                    actual = route.get("impl_"+key) if key != "latency_cycles" else None
                    domain = "routed"
                else:
                    actual = number(row.get(key))
                    domain = "HLS"
                    if key == "latency_cycles" and len(rtl_by_parent.get(row["id"], [])) == 1:
                        _, actual = rtl_by_parent[row["id"]][0]
                        domain = "RTL"
                source = (rtl_by_parent[row["id"]][0][0] if domain == "RTL" and operation != "cosim"
                          else row["id"])
                deviation = 100*(actual/expected-1) if actual is not None and expected else None
                estimates.append({"id": row["id"], "metric": key, "estimate": expected,
                                  "actual": actual, "actual_domain": domain, "deviation_pct": deviation,
                                  "actual_source": source,
                                  "over20pct": abs(deviation) > 20 if deviation is not None else None,
                                  "md_path": row["md_path"],
                                  "caveat": "Paper architecture cycles predict RTL; HLS is a component lower bound"
                                  if key == "latency_cycles" and domain == "HLS" else ""})
        parts = dsp_composition(row, config)
        if parts and config.get("stage") != "rom_clock_ws0":
            composition.append(parts)
        channels = archive/"profiling/channels.csv"
        if channels.is_file():
            with channels.open(newline="") as source:
                for channel in csv.DictReader(source):
                    if any(name in channel["name"] for name in ("features", "windows", "raster", "top", "bottom")):
                        fifos.append({"id": row["id"], "parent_design": parent,
                                      "rtl_cycles": physical.get("rtl_latency_max"), **channel})
        for path in sorted(archive.glob("*_host_memory.csv")):
            with path.open(newline="") as source:
                samples = list(csv.DictReader(source))
            if samples:
                memory.append({"id": row["id"], "operation": path.stem.removesuffix("_host_memory"),
                               "samples": len(samples),
                               "peak_process_tree_rss_GiB": max(float(item["task_tree_rss_kib"]) for item in samples)/1048576
                               if "task_tree_rss_kib" in samples[0] else None,
                               "minimum_available_GiB": min(float(item["available_kib"]) for item in samples)/1048576,
                               **swap_summary(samples)})
    reload_rows = reload_transactions(records, comparisons)
    add_frame_timings(comparisons, reload_rows)
    outputs = (("rom_clock_comparison.csv", comparisons), ("rom_clock_estimates.csv", estimates),
               ("rom_clock_dsp.csv", composition), ("rom_clock_fifo.csv", fifos), ("rom_clock_memory.csv", memory))
    for filename, rows in outputs:
        columns = list(rows[0]) if rows else ["id"]
        write_csv(ROOT/"experiments"/filename, rows, columns)
    write_csv(ROOT/"experiments/reload_switch_measurements.csv", reload_rows,
              list(reload_rows[0]) if reload_rows else ["id"])


if __name__ == "__main__":
    main()
