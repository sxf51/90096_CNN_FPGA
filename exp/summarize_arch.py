#!/usr/bin/env python3
"""Render the architecture evidence index from archived data."""
import csv
import json
import math
from pathlib import Path
from run_exp import ROOT, markdown_table, number, utc

DESCRIPTIONS = {
    "P": "Signed INT8 packing is exact when shared operands, field range and negative borrowing are handled explicitly. P01 exhausts16777216 signed8 triples; P03/P06 compare unpack-every7/every2 schedules under their respective safe bounds. P05 tests the DSP builtin and P08 inspects actual primitive attributes. Full-network exact10 residual variants retain the passing precision point but add fabric and pipeline overhead. Uniform w8a8 remains rejected by first-phase precision evidence.",
    "W": "G2=2G makes the F2 inverse exactly divisible by4 before the ordinary layer cast. W01/W03 confirm one DSP per transformed product at10/16-bit operands. The layer and network designs retain complete transform precision, split9x9 into nine3x3 pieces, generate128x128 tiles and reorder two rows into raster streams. Equivalent offline tensors are archived; runtime transforms preserve the fixed incoming-weight contract. Header-order compilation failures and independent retries remain visible.",
    "G": "Three Conv3 organizations share precision,T32 and10ns. Gather keeps four channel-wide lines; explicit-pad scatter keeps five32-bit partial rows plus a channel-wide pad row; merged-edge scatter replaces replicate padding with nine exact source-position kernels. Every output and border is checked on two butterfly frames. Memory savings carry control, load and cycle costs.",
    "S": "Whole-network DATAFLOW is compared to sequential layers and8/16/32/64 output tiles. S01 did not export the required global scratch AXI bundles and is invalid as a DDR implementation; its oversized on-chip result is retained. Tile fusion preserves Conv3 replicate semantics by clamping feature centers before their input neighborhoods, and counts complete partial-edge halos. DDR payload divided by19.2GB/s (DS98764-bit DDR4-2400) and9.6GB/s (assumed50% efficiency) is a lower-bound model, never measured bandwidth. Requested256-word bursts are distinguished from actual compiler inference in bursts.csv.",
    "C": "Exact Winograd Conv1 combines with output-channel packing Conv2 and/or adjacent-pixel packing Conv3. The paper T4 MAC budgets are932 DSP for both packed layers and1188 for only packed Conv3, before interfaces/converters. Exact10 residual restoration avoids the failed uniform INT8 precision point but adds LUT cost. A T8 control trades raster FIFO BRAM for LUTRAM. HLS estimates include transform/load/reorder overhead.",
    "F": "Storage controls map shallow wide FIFOs to LUTRAM and Conv3 line banks to20 URAM. Continuous engines separate window generation, flatten pixel/fold iterations, shift fixed channel registers and register balanced fabric reductions. Old padding versus online read/emit padding isolates finite-FIFO row serialization. Clock/T controls test actual II, resource and timing limits; final RTL and routed measurements are separate from HLS estimates.",
}


def linked(rows):
    return [{**row,"id":"["+row["id"]+"]("+row["md_path"]+")"} for row in rows]


def measured_direction(points):
    frames = [row for row in points if row["scope"] == "frame" and number(row["latency_ms_est"]) is not None]
    accepted = sorted([row for row in frames if row["eligible_provisional"] == "True"],
                      key=lambda row:number(row["latency_ms_est"]))
    if accepted:
        best = accepted[0]
        return "Measured direction result: ["+best["id"]+"]("+best["md_path"]+") is its fastest provisional resource-feasible point at "+best["latency_ms_est"]+"ms, with "+best["DSP"]+" DSP and "+best["LUT"]+" LUT. RTL and routing must be assessed separately.\n\n"
    if frames:
        return "Measured direction result: none of its completed frame points satisfies all resource/precision gates. Their estimated latency cannot establish a feasible speedup.\n\n"
    return "Completed PE/layer evidence is listed below; it does not establish a resource-feasible frame design.\n\n"


def main():
    rows = list(csv.DictReader((ROOT / "experiments/architecture_data.csv").open(newline="")))
    arch = [row for row in rows if row["series"]]
    frames = [row for row in rows if row["scope"] == "frame" and not row["operation"] and
              row.get("validation_only") != "True" and
              (row["series"] or "dataflow" in row["design"] or "scatter" in row["design"])]
    frames.sort(key=lambda row:number(row["latency_ms_est"]) if number(row["latency_ms_est"]) is not None else math.inf)
    eligible = [row for row in frames if row["eligible_provisional"] == "True"]
    best = eligible[0] if eligible else None
    text = "# SRCNN K26 architecture exploration\n\n"
    text += ("The fastest resource-feasible supplied-image point is ["+best["id"]+"]("+best["md_path"]+") at "+best["latency_ms_est"]+"ms HLS-estimated latency. " if best else "No resource-feasible exact frame point is currently available. ")
    text += "Packing and integer Winograd primitives pass exact checks, while full-network results include fabric, memory and scheduling costs absent from DSP-only budgets. Missing comic keeps every precision acceptance provisional; routed timing, RTL cycles and board validation are distinct evidence.\n\n"
    text += "Re-run frozen HLS records with fresh IDs using the [reproduction guide](REPRODUCE.md). Original reserved IDs remain immutable.\n\n"
    if best:
        text += "## Current Best\n\n"+markdown_table(linked([best]),[
            "id","design","precision_w_a_acc","T_target","clock_target_ns","clock_est_ns","latency_cycles",
            "interval_cycles","latency_ms_est","DSP","BRAM18K","URAM","LUT","FF","delta_psnr","status"])
        baseline = next((row for row in rows if row["id"] == "E043"),None)
        if baseline and number(best["latency_ms_est"]):
            ratio = number(baseline["latency_ms_est"])/number(best["latency_ms_est"])
            text += "\nHLS-estimate improvement over first-phase E043: "+str(round(ratio,4))+"x. This ratio is not a measured board speedup.\n"
        related = []
        for row in rows:
            path = ROOT / "experiments" / Path(row["md_path"]).parent / "config.json"
            config = json.loads(path.read_text())
            if config.get("verify_parent") == best["id"]:
                related.append({**row,**config.get("verification",{})})
        text += "\nActual verification of the current HLS winner:\n\n"+markdown_table(linked(related),[
            "id","operation","status","impl_WNS_ns","timing_met","impl_DSP","impl_LUT","impl_FF",
            "impl_BRAM36","impl_URAM","rtl_status","rtl_latency_max","rtl_interval_max","cycle_deviation_pct"])
    for series in ("P","W","G","S","C","F"):
        points = [row for row in arch if row["series"] == series and not row["operation"]]
        text += "\n## "+series+" Direction\n\n"+DESCRIPTIONS[series]+"\n\n"
        text += measured_direction(points)
        text += markdown_table(linked(points),["id","scope","T_target","latency_cycles","latency_ms_est",
                                               "DSP","BRAM18K","URAM","LUT","FF","bit_exact","border_mse","ii_ok","status"])
        if series == "S":
            text += "\nTraffic/cache models and inferred image burst lengths (words):\n\n"
            text += markdown_table(linked(points),[
                "id","ddr_bytes_per_frame","feature_recompute_ratio","cache_bits",
                "inferred_image_read_bursts","inferred_image_write_bursts",
                "ddr_theoretical_lower_bound_ms","ddr_50pct_lower_bound_ms","status"])
            text += "\nBandwidth inputs are from [DS987 and calculation sources](SOURCES.md). S01's traffic is a hypothetical sequential-DDR payload because its scratch ports were absent; tile/dataflow payloads describe their implemented interfaces. Missing burst inference is shown as 'none reported'; requested256-word limits remain configuration bounds.\n"
    text += "\n## All Architectures\n\nFrame records only, ordered by HLS-estimated latency. Microkernels and validation operations are excluded; infeasible/failed results remain visible.\n\n"
    text += markdown_table(linked(frames),["id","series","design","T_target","latency_ms_est","DSP","BRAM18K","LUT","FF","delta_psnr","status"])
    comparisons = list(csv.DictReader((ROOT / "experiments/estimate_actual.csv").open(newline="")))
    audits = {}
    for row in comparisons:
        record = audits.setdefault(row["id"],{"id":row["id"],"series":row["series"],"scope":row["scope"],"md_path":row["md_path"],"status":row["status"]})
        if row["metric"] in {"DSP","latency_cycles"}:
            key = "DSP" if row["metric"] == "DSP" else "cycles"
            record[key+"_estimate"],record[key+"_actual"],record[key+"_deviation_pct"] = row["estimate"],row["actual"],row["deviation_pct"]
    text += "\n## Estimates And Actuals\n\nAll numeric values come from frozen plans and parsed reports. Actual means csynth for ordinary runs, routed resources for implementation, and RTL latency for cosim; no cycle measurement is inferred from implementation. Memory/LUT audits are in estimate_actual.csv and each experiment.\n\n"
    text += markdown_table(linked(list(audits.values())),["id","scope","DSP_estimate","DSP_actual","DSP_deviation_pct","cycles_estimate","cycles_actual","cycles_deviation_pct","status"])
    largest = sorted([row for row in comparisons if row["over20pct"] == "True"],
                     key=lambda row:abs(number(row["deviation_pct"]) or 0),reverse=True)[:12]
    text += "\nLargest percentage deviations (a zero paper denominator has no percentage):\n\n"
    text += markdown_table(linked(largest),["id","metric","estimate","actual","deviation_pct","status"])
    text += "\nCause analysis is in each linked interpretation: ignored external scratch ports allocate full on-chip maps; dynamic tiled memory banks add address/multiplexer logic; packing residual/borrow stages increase both LUT and per-pixel pipeline drain; wider Winograd inverse arithmetic and raster FIFOs exceed pure-product budgets; explicit register reductions change timing and FF.\n"
    verification = []
    for row in rows:
        if not row["operation"]:
            continue
        path = ROOT / "experiments" / Path(row["md_path"]).parent / "config.json"
        config = json.loads(path.read_text())
        verification.append({**row, "parent":config.get("verify_parent"), **config.get("verification",{})})
    text += "\n## Implementation And Cosim\n\nHLS estimates are inherited only for provenance. Routed WNS/resources and two-frame RTL cycles are parsed independently; none is a board measurement.\n\n"
    text += markdown_table(linked(verification),["id","scope","parent","operation","status","impl_DSP","impl_BRAM36","impl_LUT","impl_FF","impl_URAM","impl_WNS_ns","timing_met","rtl_status","rtl_latency_max","rtl_interval_max","cycle_deviation_pct"])
    warning_points = [row for row in arch if number(row.get("dataflow_warning_count")) and not row["operation"]]
    text += "\nDATAFLOW warnings are retained in [dataflow_warnings.csv](dataflow_warnings.csv) and the linked experiment interpretations. Caller-weight/predecessor synchronization is a possible throughput limit; reported II1 alone does not prove finite-FIFO progress.\n\n"
    text += markdown_table(linked(warning_points),["id","dataflow_warning_count","status"])
    selection_path = ROOT / "experiments/final_selection.json"
    if selection_path.is_file():
        selection = json.loads(selection_path.read_text())
        selected_ids = {point["id"] for point in selection["selected"]}
        validation = []
        for row in rows:
            if row["id"] not in selection["queue"] or row["operation"]:
                continue
            config = json.loads((ROOT / "experiments" / Path(row["md_path"]).parent / "config.json").read_text())
            validation.append({**row,**config.get("validation",{})})
        text += "\nSelected candidates were ranked globally across both phases before validation. Mandatory full-supplied-image C simulation:\n\n"
        text += markdown_table(linked(validation),["id","design","image_count","csim_pass","bit_exact","set14_psnr","delta_psnr","border_mse","status"])
        relevant = [record for record in verification if record["parent"] in selected_ids]
        text += "\nRouted timing closes for "+str(sum(str(record.get("timing_met")).lower() == "true" for record in relevant))+" selected implementation runs; "+str(sum(record.get("rtl_status") == "Pass" and record["status"] == "cosim_complete" for record in relevant))+" selected two-frame RTL runs pass. Completion of a route with negative WNS is retained as a timing failure.\n"
    failed = [row for row in arch if row["status"] not in {"pass","provisional","csim_pass","impl_complete","cosim_complete","analysis_complete"}]
    text += "\n## Failed Directions\n\n"+markdown_table(linked(failed),["id","series","status","failure_reason","notes"])
    text += "\n## Pending Human Decisions\n\n"
    text += "- Supply the missing comic pair before complete14-image precision acceptance. All13 supplied pairs remain mandatory.\n"
    text += "- DDR sequential layers need explicit scratch pointers or an approved wrapper; global m_axi did not export ports in S01.\n"
    text += "- Runtime transformed-weight loading preserves the frozen top signature; true offline-transformed input parameters require an approved new weight contract.\n"
    text += "- Windows settings-batch execution and board integration remain unverified. The existing Linux Vitis2026.1 SSH installation was used.\n"
    text += "- Review normalized-float PSNR against the original wrapping uint8 metric before external benchmark claims. See [LOG.md](LOG.md).\n"
    text += "\n## Next Steps\n\nUse the best exact resource-feasible architecture as the integration candidate only after checking routed slack and finite-FIFO RTL evidence. Prioritize the measured limiting loop/path or memory bank; retain strict precision, border and resource gates. Complete the missing image and board/AXI system measurements before claiming deployable performance.\n"
    audit = ROOT / "experiments/architecture_audit.json"
    if audit.is_file():
        audit_data = json.loads(audit.read_text())
        text += "\n## Integrity Audit\n\nFinal local/remote original and first-phase source checksum audit: [architecture_audit.json](architecture_audit.json).\n\n"
        text += markdown_table(audit_data["checks"],["location","manifest","checked_files","pass"])
    text += "\n## Figures\n\n"
    for name,label in (("architecture_pareto","Latency vs DSP by series"),("architecture_dsp_layers","DSP composition"),
                       ("estimate_actual_dsp","DSP estimates vs actual"),("estimate_actual_cycles","Cycle estimates vs actual"),
                       ("conv3_resources","Conv3 resource comparison"),
                       ("conv3_core_resources","Conv3 core and pad resource comparison")):
        text += "!["+label+"](figs/"+name+".png)\n\n"
    text += "Generated from archived evidence at "+utc()+".\n"
    (ROOT / "experiments/ARCH_SUMMARY.md").write_text(text)
    summary = ROOT / "experiments/SUMMARY.md"
    original = summary.read_text()
    link = "Architecture exploration: [ARCH_SUMMARY.md](ARCH_SUMMARY.md).\n\n"
    if not original.startswith(link):
        summary.write_text(link+original)
    print("Wrote ARCH_SUMMARY.md;",len(arch),"architecture records;")


if __name__ == "__main__":
    main()
