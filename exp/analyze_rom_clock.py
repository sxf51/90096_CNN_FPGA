#!/usr/bin/env python3
"""Derive docs/0005 comparisons without rewriting historical result statuses."""
import csv
import json
from analyze_arch import dsp_composition, write_csv
from run_exp import ROOT, number
from route_gates import archive_route_evidence

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


def main():
    state = json.loads((ROOT/"experiments/rom_clock_state.json").read_text())
    records = [item for exp_id in dict.fromkeys(["W21", "F97", "F98", "W22"] + state["experiment_ids"])
               if (item := load(exp_id)) is not None]
    rtl_by_parent = {}
    for archive, row, config in records:
        measured = number(config.get("verification", {}).get("rtl_latency_max"))
        if config.get("operation") == "cosim" and row["status"] == "cosim_complete" and measured is not None:
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
            accepted_rtl = record["rtl_cycles"] if record["rtl_source"] or row["status"] == "cosim_complete" else None
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
                               "minimum_available_GiB": min(float(item["available_kib"]) for item in samples)/1048576})
    outputs = (("rom_clock_comparison.csv", comparisons), ("rom_clock_estimates.csv", estimates),
               ("rom_clock_dsp.csv", composition), ("rom_clock_fifo.csv", fifos), ("rom_clock_memory.csv", memory))
    for filename, rows in outputs:
        columns = list(rows[0]) if rows else ["id"]
        write_csv(ROOT/"experiments"/filename, rows, columns)


if __name__ == "__main__":
    main()
