#!/usr/bin/env python3
"""Current docs/0005 workstream evidence, preserving historical experiment rows."""
import csv
import json
from analyze_arch import write_csv
from run_exp import ROOT, markdown_table, number, utc
from route_gates import archive_route_evidence
from rtl_acceptance import accepted_cosim, acceptance_basis


def pending_experiments(state):
    records = []
    for exp_id in state["experiment_ids"]:
        if list((ROOT / "experiments").glob(exp_id + "_*/metrics.json")):
            continue
        plans = list((ROOT / "experiments").glob(exp_id + "_*/plan.json"))
        if len(plans) != 1:
            raise RuntimeError("Expected one unmeasured plan for " + exp_id)
        config = json.loads(plans[0].read_text())["configuration"]
        waiting = exp_id in state.get("waiting_for_memory", [])
        skipped = state.get("skipped_plans", {}).get(exp_id)
        records.append({"id": exp_id, "parent": config.get("verify_parent", config.get("control_experiment")),
                        "operation": config.get("operation", "csim/csynth"),
                        "status": ("not_run_condition_failed" if skipped else "unlaunched_memory" if waiting else "unlaunched_conditional"
                                   if exp_id in state.get("unlaunched_ids", []) else "queued_or_running"),
                        "condition": skipped["reason"] if skipped else state.get("planned_conditions", {}).get(exp_id),
                        "md_path": plans[0].parent.name + "/" + exp_id + ".md"})
    return records


def completed_rtl_matches(parent):
    matches = []
    for cp in (ROOT / "experiments").glob("*_*/config.json"):
        candidate = json.loads(cp.read_text())
        if candidate.get("operation") != "cosim" or candidate.get("verify_parent") != parent:
            continue
        metrics = json.loads(cp.with_name("metrics.json").read_text())
        cycles = number(candidate.get("verification", {}).get("rtl_latency_max"))
        if accepted_cosim(metrics, candidate) and cycles is not None:
            matches.append((candidate["id"], cycles))
    return matches


def main():
    state = json.loads((ROOT / "experiments/rom_clock_state.json").read_text())
    comparison_path = ROOT / "experiments/rom_clock_comparison.csv"
    comparisons = list(csv.DictReader(comparison_path.open(newline=""))) if comparison_path.is_file() else []
    comparison_by_id = {row["id"]: row for row in comparisons}
    rows = []
    for exp_id in state["experiment_ids"]:
        paths = list((ROOT / "experiments").glob(exp_id + "_*/metrics.json"))
        if not paths:
            continue
        path = paths[0]
        row = json.loads(path.read_text())
        config = json.loads(path.with_name("config.json").read_text())
        physical = config.get("verification", {})
        route = archive_route_evidence(path.parent) if config.get("operation") == "impl" else {}
        record = {"id": exp_id, "parent": config.get("verify_parent", config.get("control_experiment")),
                  "operation": config.get("operation", "csim" if config.get("csim_only") else "csim/csynth"),
                  "status": row["status"], "md_path": row["md_path"],
                  "bit_exact": row.get("bit_exact"), "delta_psnr": row.get("delta_psnr"),
                  "HLS_cycles": row.get("latency_cycles"), "HLS_DSP": row.get("DSP"),
                  "HLS_LUT": row.get("LUT"), "route_feasible": route.get("route_feasible"),
                  "route_clock_ns": physical.get("impl_target_clock_ns"),
                  "route_WNS_ns": route.get("impl_WNS_ns"), "route_WHS_ns": route.get("impl_WHS_ns"),
                  **{key: route.get("impl_" + key) for key in ("DSP", "BRAM18K", "URAM", "LUT", "FF")},
                  "rtl_cycles": physical.get("rtl_latency_max"), "rtl_source": None,
                  "rtl_accepted": accepted_cosim(row, config) if config.get("operation") == "cosim" else None,
                  "rtl_acceptance_basis": acceptance_basis(row, config) if config.get("operation") == "cosim" else None,
                  "rtl_hls_excess_pct": comparison_by_id.get(exp_id, {}).get("rtl_hls_excess_pct"),
                  "wsD_goal_met": comparison_by_id.get(exp_id, {}).get("wsD_goal_met"),
                  "rtl_cycles_x_route_clock_ms": None}
        if config.get("operation") == "impl" and route.get("route_feasible") is True:
            parent = config["verify_parent"]
            matches = completed_rtl_matches(parent)
            if len(matches) == 1:
                record["rtl_source"], record["rtl_cycles"] = matches[0]
                record["rtl_cycles_x_route_clock_ms"] = record["rtl_cycles"] * record["route_clock_ns"] / 1e6
        rows.append(record)
    columns = list(rows[0]) if rows else ["id", "status", "route_feasible"]
    write_csv(ROOT / "experiments/rom_clock_workstream.csv", rows, columns)
    text = "# ROM, clock, FIFO and T4 workstream\n\n"
    text += "Plan: [docs/0005](../docs/0005-rom-clock-t4-plan.md). Updated " + utc() + ".\n\n"
    text += ("The user-accepted F47/F48 deep-window design is the T8 mainline basis; W21 remains the independently routed integration fallback. "
             "ROM is an independent experiment. Set14 means the complete 13-image course-provided set. ")
    text += "Final resource acceptance uses independent OOC routed timing/utilization; archived HLS statuses are unchanged. No board performance is inferred.\n\n"
    text += "## Current state\n\n" + state["phase"] + ". " + state["next"] + "\n\n"
    display_columns = ["id", "parent", "operation", "status", "bit_exact", "delta_psnr", "HLS_cycles",
                       "HLS_DSP", "HLS_LUT", "rtl_cycles", "rtl_acceptance_basis", "route_clock_ns", "route_feasible",
                       "rtl_cycles_x_route_clock_ms", "rtl_hls_excess_pct", "wsD_goal_met"]
    text += markdown_table([{**row, "id": "[" + row["id"] + "](" + row["md_path"] + ")"} for row in rows], display_columns)
    text += "\nMissing measurements are unknown. A frame time is shown only for independently closed/resource-feasible routing plus matching-parent measured RTL cycles.\n"
    text += "\nWS-D performance is separate from a successful functional cosimulation. With the525237-cycle HLS bound, "
    text += "the2% goal allows at most535741 integer RTL cycles (535741.74 before flooring); never round the threshold upward.\n"
    text += "User revision in docs/0005 section6.2 accepts F48 as the new mainline basis despite its30-cycle diagnostic miss, and accepts faster W28 under the original upper bound only. Original result statuses and paper plans remain unchanged; the explicit acceptance basis records this authorization.\n"
    pending = pending_experiments(state)
    text += "\n## Unmeasured plans\n\n"
    text += markdown_table([{**row, "id": "[" + row["id"] + "](" + row["md_path"] + ")"} for row in pending],
                           ["id", "parent", "operation", "status", "condition"])
    text += "\nThese plans have no result row. In particular, unlaunched implementation is neither a timeout nor a timing failure.\n"
    if comparison_path.is_file():
        accepted = [row for row in comparisons if row["route_feasible"] == "True" and
                    number(row["rtl_frame_ms"]) is not None]
        accepted.sort(key=lambda row: number(row["rtl_frame_ms"]))
        text += "\n## Verified IP timing\n\n"
        text += markdown_table([{**row, "id": "[" + row["id"] + "](" + row["md_path"] + ")"} for row in accepted],
                               ["id", "parent", "rtl_source", "rtl_cycles", "route_clock_ns", "route_WNS_ns",
                                "route_DSP", "route_BRAM18K", "route_LUT", "route_FF", "rtl_frame_ms"])
        text += "\nIP times exclude DDR, driver and board overhead. W21 remains the runtime-loaded integration fallback.\n"
    handoffs = state.get("candidate_board_handoffs", {})
    if handoffs:
        text += "\nVerified candidate IP packages and register maps: "
        text += ", ".join("["+exp_id+"]("+str((ROOT/path).relative_to(ROOT/"experiments"))+")"
                          for exp_id, path in handoffs.items())
        text += ". Retain the [F98 integration handoff](BOARD_HANDOFF.md); board verification is pending.\n"
    text += "\n## Figures\n\n"
    for filename, label in (("rom_clock_pareto", "HLS screening"), ("rom_clock_dsp", "DSP composition"),
                            ("rom_clock_estimate_DSP", "DSP estimates and measurements"),
                            ("rom_clock_estimate_latency_cycles", "Cycle estimates and measurements"),
                            ("rom_clock_rtl_cycles", "Two-frame RTL cycles")):
        if (ROOT / "experiments/figs" / (filename + ".png")).exists():
            text += "![" + label + "](figs/" + filename + ".png)\n\n"
    overlap_path = ROOT / "experiments/parallel_overlap.csv"
    if overlap_path.is_file():
        overlaps = list(csv.DictReader(overlap_path.open(newline="")))
        text += "\n## Measured Parallel Execution\n\n"
        text += ("Current policy permits one heavy task with light jobs subject to registered budgets and actual memory headroom. "
                 "The earlier two-heavy overlap failures remain visible. Completed tool intervals and per-task telemetry are in "
                 "[parallel_jobs.csv](parallel_jobs.csv) and [parallel_overlap.csv](parallel_overlap.csv). "
                 "Active tasks enter these tables only after a release record is archived.\n\n")
        text += markdown_table(overlaps, ["first_id", "second_id", "overlap_seconds", "aligned_samples",
                                          "peak_combined_process_tree_rss_GiB", "minimum_available_GiB", "cpu_busy_pct"])
        text += "\nProcess-tree RSS sums include shared mappings; minimum MemAvailable is measured for the entire host. Sampling alignment tolerance is4seconds. A hatch marks nonzero tool exit, not failed timing closure.\n"
        if (ROOT / "experiments/figs/parallel_timeline.png").is_file():
            text += "\n![Measured task intervals](figs/parallel_timeline.png)\n"
    text += "\n## Pending human decisions / 待人工决策\n\n"
    text += "\n".join("- " + decision for decision in state.get("pending_decisions", [])) + "\n"
    (ROOT / "experiments/ROM_CLOCK.md").write_text(text)
    plan_path = ROOT / state["plan"]
    plan_text = plan_path.read_text()
    marker = "<!-- ROM_CLOCK_MEASUREMENTS -->"
    if marker in plan_text:
        plan_text = plan_text.split(marker, 1)[0].rstrip() + "\n"
    section = "\n" + marker + "\n\n### 自动归档的进展\n\n"
    section += "完整指标和解读见 [ROM_CLOCK.md](../experiments/ROM_CLOCK.md)；下表数字由报告解析生成。\n\n"
    section += markdown_table([{**row, "id": "[" + row["id"] + "](../experiments/" + row["md_path"] + ")"}
                               for row in rows if row["id"] not in {"F32", "F33", "F34", "F36", "F37", "F38"}],
                              ["id", "parent", "status", "HLS_cycles", "HLS_DSP", "HLS_LUT", "rtl_cycles",
                               "route_feasible", "rtl_cycles_x_route_clock_ms"])
    section += "\n未测量的计划：\n\n" + markdown_table(pending, ["id", "parent", "status", "condition"])
    plan_path.write_text(plan_text + section)
    progress = ROOT / "experiments/PROGRESS.md"
    old = progress.read_text()
    marker = "<!-- ROM_CLOCK_CURRENT -->"
    if marker in old:
        old = old.split(marker, 2)[-1].lstrip("\n")
    block = marker + "\n\n## Active docs/0005 workstream\n\n" + state["phase"] + ". " + state["next"]
    block += "\n\nSee [ROM_CLOCK.md](ROM_CLOCK.md) and [rom_clock_state.json](rom_clock_state.json). "
    policy = ("one heavy task with light jobs admitted by measured headroom" if state.get("concurrency_policy") == "one_heavy_with_light"
              else "serial hardware fallback after measured OOM; two-task policy retained" if state.get("hardware_serial_after_oom")
              else "explicit two-task scheduling with actual memory telemetry" if state.get("concurrency_policy") == "user_two_jobs"
              else "budgeted after WS-0 validation")
    block += "Current gates override historical missing-comic/HLS-only/serial-lock wording below: complete course Set14=13; final feasibility=routed; concurrency=" + policy + ".\n\n" + marker + "\n\n"
    progress.write_text("# Current progress\n\n" + block + old.removeprefix("# Current progress\n\n"))


if __name__ == "__main__":
    main()
