#!/usr/bin/env python3
"""Current docs/0005 workstream evidence, preserving historical experiment rows."""
import json
from analyze_arch import write_csv
from run_exp import ROOT, markdown_table, number, utc
from route_gates import archive_route_evidence


def main():
    state = json.loads((ROOT / "experiments/rom_clock_state.json").read_text())
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
                  "rtl_cycles_x_route_clock_ms": None}
        if config.get("operation") == "impl" and route.get("route_feasible") is True:
            parent = config["verify_parent"]
            matches = []
            for cp in (ROOT / "experiments").glob("*_*/config.json"):
                candidate = json.loads(cp.read_text())
                cycles = number(candidate.get("verification", {}).get("rtl_latency_max"))
                if candidate.get("operation") == "cosim" and candidate.get("verify_parent") == parent and cycles is not None:
                    matches.append((candidate["id"], cycles))
            if len(matches) == 1:
                record["rtl_source"], record["rtl_cycles"] = matches[0]
                record["rtl_cycles_x_route_clock_ms"] = record["rtl_cycles"] * record["route_clock_ns"] / 1e6
        rows.append(record)
    columns = list(rows[0]) if rows else ["id", "status", "route_feasible"]
    write_csv(ROOT / "experiments/rom_clock_workstream.csv", rows, columns)
    text = "# ROM, clock, FIFO and T4 workstream\n\n"
    text += "Plan: [docs/0005](../docs/0005-rom-clock-t4-plan.md). Updated " + utc() + ".\n\n"
    text += "Runtime-loaded W21 remains the mainline. ROM is an independent experiment. Set14 means the complete 13-image course-provided set. "
    text += "Final resource acceptance uses independent OOC routed timing/utilization; archived HLS statuses are unchanged. No board performance is inferred.\n\n"
    text += "## Current state\n\n" + state["phase"] + ". " + state["next"] + "\n\n"
    text += markdown_table([{**row, "id": "[" + row["id"] + "](" + row["md_path"] + ")"} for row in rows], columns)
    text += "\nMissing measurements are unknown. A frame time is shown only for independently closed/resource-feasible routing plus matching-parent measured RTL cycles.\n"
    text += "\n## Pending human decisions / 待人工决策\n\n"
    text += "\n".join("- " + decision for decision in state.get("pending_decisions", [])) + "\n"
    (ROOT / "experiments/ROM_CLOCK.md").write_text(text)
    progress = ROOT / "experiments/PROGRESS.md"
    old = progress.read_text()
    marker = "<!-- ROM_CLOCK_CURRENT -->"
    if marker in old:
        old = old.split(marker, 2)[-1].lstrip("\n")
    block = marker + "\n\n## Active docs/0005 workstream\n\n" + state["phase"] + ". " + state["next"]
    block += "\n\nSee [ROM_CLOCK.md](ROM_CLOCK.md) and [rom_clock_state.json](rom_clock_state.json). "
    block += "Current gates override historical missing-comic/HLS-only/serial-lock wording below: complete course Set14=13; final feasibility=routed; concurrency=budgeted after WS-0 validation.\n\n" + marker + "\n\n"
    progress.write_text("# Current progress\n\n" + block + old.removeprefix("# Current progress\n\n"))


if __name__ == "__main__":
    main()
