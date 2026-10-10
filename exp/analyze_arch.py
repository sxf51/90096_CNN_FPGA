#!/usr/bin/env python3
"""Derive architecture comparison CSVs and report-based estimate audits."""
import csv
import json
import math
import re
from pathlib import Path
from run_exp import ROOT, markdown_table, number

SERIES_NOTES = {
    "S": "Whole-network DATAFLOW overlaps the dedicated layer engines. Tile fusion removes full feature maps but executes Conv1/Conv2 and Conv3 sequentially, recomputes halos, and can lose memory parallelism. Requested AXI burst limits are upper bounds; only inferred bursts are evidence of burst generation. DDR payload/bandwidth models exclude protocol stalls and are lower bounds.",
    "G": "Scatter trades the channel-wide gather line/window storage for five32-bit partial rows and a5x5 register window. Explicit padding retains a32-channel row; merged edge kernels remove it but introduce nine coefficient classes, wider coefficients, selection and runtime merge work. Equality of every butterfly output, including six-pixel borders and the repeated frame, is the padding gate.",
    "P": "Two products share one DSP only when operand packing and signed-low borrowing are handled explicitly. Exact ten-bit coefficient residuals add fabric control/adders, and adjacent-pixel Conv3 needs a5x6 window plus odd-column disposal. Extra multiplier/pipeline depth is paid on every pixel in nested fold schedules. PE cycle counts cannot be interpreted as network-frame times.",
    "W": "Integer G2 preserves exact products and performs an exact divide-by-four before the original layer cast. Wider transforms and inverse additions, nine subkernels, runtime weight transforms and two raster row FIFOs are outside a multiplication-only budget. The128x128 tile grid computes65536 output positions before discarding the511 extra positions. PE/layer results do not establish full-network feasibility.",
    "C": "The combination retains Winograd Conv1 and uses packing only on other layers, avoiding incompatible transformed INT8 operands. Multiplier budgets omit residual/borrow correction, inverse arithmetic, runtime transformed weights and raster reorder. Dedicated layer resource counts must be summed once; nested child reports repeat their parents' resources.",
    "F": "Continuous scheduling separates window generation and MAC folds, shifts channel registers and explicitly registers fabric reduction trees. This can remove pixel fill/drain but costs pipeline registers and wide window FIFOs. Online padding overlaps source reads with padded writes; old row serialization can create finite-FIFO stalls absent from maximum-component HLS estimates. RTL cycles and routed slack remain the final evidence.",
}


def write_csv(path, rows, columns):
    with path.open("w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def scope(config, row):
    if config.get("operation"):
        return config.get("scope", "frame")
    if config.get("scope") in {"PE", "layer", "frame"}:
        return config["scope"]
    if "micro" in row["design"]:
        return "PE"
    return "frame"


def eligible(row, config):
    return (scope(config,row) == "frame" and not config.get("operation") and
            row["status"] in {"pass", "provisional"} and str(row["csim_pass"]).lower() == "true" and
            (not config.get("fixed") or
             (str(row["bit_exact"]).lower() == "true" and number(row["delta_psnr"]) is not None and
              number(row["delta_psnr"]) >= -.1)))


def module_for(modules, layer):
    preferred = ("conv1_stream", "conv1_tiles", "engine1") if layer == 1 else (
        ("conv2_stream", "engine2") if layer == 2 else ("conv3_stream", "engine3"))
    for name in preferred:
        found = [module for module in modules if module["module"] == name]
        if found:
            return found[0]
    return None


def main():
    rows = list(csv.DictReader((ROOT / "experiments/results.csv").open(newline="")))
    structures, estimates, composition, bursts, conv3 = [], [], [], [], []
    for row in rows:
        archive = ROOT / "experiments" / Path(row["md_path"]).parent
        path = archive / "config.json"
        if not path.is_file():
            continue
        config = json.loads(path.read_text())
        derived = {**row, "scope": scope(config,row), "operation": config.get("operation", ""),
                   "eligible_provisional": eligible(row,config),
                   "ddr_bytes_per_frame": config.get("ddr_bytes_per_frame", ""),
                   "feature_recompute_ratio": config.get("feature_recompute_ratio", ""),
                   "cache_bits": config.get("cache_bits", ""),
                   "inferred_image_read_bursts": "", "inferred_image_write_bursts": ""}
        logs = archive / "csynth.log.txt"
        if logs.is_file():
            observed = re.findall(r"burst (reads|writes) of length (\d+) and bit width (\d+) in loop '([^']+)'[^\n]*?on bundle '([^']+)'",logs.read_text())
            for direction, count, bits, loop, bundle in observed:
                bursts.append({"id": row["id"], "direction": direction, "bundle": bundle,
                               "inferred_words": count, "word_bits": bits, "loop": loop,
                               "note": "Inference length may be partitioned by AXI max burst settings"})
            for direction, key in (("reads","inferred_image_read_bursts"),("writes","inferred_image_write_bursts")):
                counts = sorted({int(count) for kind,count,_,_,bundle in observed if kind == direction and bundle in {"image_in","image_out"}})
                derived[key] = "/".join(map(str,counts)) if counts else "none reported"
        bandwidth = config.get("ddr_lower_bound_ms", [])
        derived["ddr_theoretical_lower_bound_ms"] = bandwidth[0] if bandwidth else ""
        derived["ddr_50pct_lower_bound_ms"] = bandwidth[1] if bandwidth else ""
        structures.append(derived)
        if not row["series"]:
            continue
        comparisons = []
        for key in ("DSP", "BRAM18K", "URAM", "LUT", "latency_cycles"):
            paper = number(config.get("estimates",{}).get(key))
            actual = number(row.get(key))
            if config.get("operation") == "impl" and key in {"DSP", "URAM", "LUT"}:
                actual = number(config.get("verification",{}).get("impl_"+key))
            if config.get("operation") == "impl" and key == "BRAM18K":
                bram36 = number(config.get("verification",{}).get("impl_BRAM36"))
                actual = 2*bram36 if bram36 is not None else None
            if config.get("operation") == "impl" and key == "latency_cycles":
                actual = None
            if config.get("operation") == "cosim" and key == "latency_cycles":
                actual = number(config.get("verification",{}).get("rtl_latency_max"))
            deviation = 100*(actual/paper-1) if actual is not None and paper else None
            item = {"id":row["id"], "series":row["series"], "scope":derived["scope"],
                    "metric":key, "estimate":paper, "actual":actual, "deviation_pct":deviation,
                    "over20pct": actual is not None and paper is not None and
                                 (actual != 0 if paper == 0 else abs(deviation) > 20),
                    "status":row["status"], "md_path":row["md_path"]}
            comparisons.append(item)
            estimates.append(item)
        modules = config.get("parsed_modules", [])
        if row["id"] in {"G01","G02","G03"}:
            kernel = module_for(modules,3)
            padding = next((module for module in modules if module["module"] == "replicate_pad_pixel2_2_s"),None)
            if kernel:
                conv3.append({"id":row["id"],"variant":{"G01":"gather","G02":"scatter_pad","G03":"scatter_edge"}[row["id"]],
                              **{"kernel_"+key:kernel.get(key) for key in ("DSP","BRAM18K","LUT","FF","latency_cycles")},
                              **{"padding_"+key:padding.get(key) if padding else 0 for key in ("DSP","BRAM18K","LUT","FF")},
                              "border_mse":row["border_mse"],"bit_exact":row["bit_exact"],"ii_ok":row["ii_ok"]})
        if derived["scope"] == "frame" and not config.get("operation") and modules:
            parts = [module_for(modules,layer) for layer in (1,2,3)]
            if all(part is not None for part in parts):
                counts = [number(part.get("DSP")) for part in parts]
                if all(count is not None for count in counts):
                    remainder = number(row["DSP"])-sum(counts)
                    if remainder < 0:
                        raise RuntimeError("Overlapping module DSP accounting: "+row["id"])
                    composition.append({"id":row["id"], "series":row["series"],
                                        "Conv1_DSP":counts[0], "Conv2_DSP":counts[1], "Conv3_DSP":counts[2],
                                        "other_DSP":remainder, "total_DSP":row["DSP"], "status":row["status"]})
        report_rows = []
        for layer in (1,2,3):
            part = module_for(modules,layer)
            if part:
                report_rows.append({"module":part["module"], "latency_cycles":part.get("latency_cycles"),
                                    "DSP":part.get("DSP"), "BRAM18K":part.get("BRAM18K"),
                                    "LUT":part.get("LUT"), "FF":part.get("FF")})
        loops = [loop for loop in config.get("parsed_loops",[]) if loop.get("actual_ii") is not None]
        md_path = archive / (row["id"]+".md")
        text = md_path.read_text()
        human = config.get("interpretation", "")+"\n\n"+SERIES_NOTES.get(row["series"], "")
        human += "\n\nEstimate audit (parsed values; zero estimates have no percentage denominator):\n\n"
        human += markdown_table(comparisons,["metric","estimate","actual","deviation_pct","over20pct"])
        if report_rows:
            human += "\nWhole layer evidence from csynth XML (child pipeline reports are not added again):\n\n"
            human += markdown_table(report_rows,["module","latency_cycles","DSP","BRAM18K","LUT","FF"])
        if loops:
            human += "\nPipeline depth and II evidence; nested pixel schedules pay the reported iteration latency at every restart:\n\n"
            human += markdown_table(loops,["module","loop","IterationLatency","PipelineDepth","actual_ii","target_ii","ii_ok"])
        if config.get("errors"):
            human += "\nObserved errors: "+"; ".join(config["errors"])+"\n"
        if row["id"] == "S01":
            human += "\nThe global arrays remained on chip because scratch1/scratch2 AXI bundles were absent. Consequently the reported memory/cycles describe an invalid on-chip probe, not an implemented DDR design. The zero external-memory BRAM assumption failed because the interface pragma was ignored. Changing the frozen top signature needs human decision.\n"
        if config.get("ddr_bytes_per_frame"):
            human += "\nDDR/burst model from configuration and synthesis logs:\n\n"+markdown_table([derived],[
                "ddr_bytes_per_frame","feature_recompute_ratio","cache_bits", "inferred_image_read_bursts",
                "inferred_image_write_bursts","ddr_theoretical_lower_bound_ms","ddr_50pct_lower_bound_ms"])
        start = text.index("## 6. Interpretation / 解读\n\n")+len("## 6. Interpretation / 解读\n\n")
        end = text.index("\n## 7. Conclusion",start)
        md_path.write_text(text[:start]+human.rstrip()+"\n"+text[end:])
    extra = ["scope","operation","eligible_provisional","ddr_bytes_per_frame","feature_recompute_ratio","cache_bits",
             "inferred_image_read_bursts","inferred_image_write_bursts","ddr_theoretical_lower_bound_ms","ddr_50pct_lower_bound_ms"]
    write_csv(ROOT / "experiments/architecture_data.csv",structures,list(rows[0])+extra)
    write_csv(ROOT / "experiments/estimate_actual.csv",estimates,["id","series","scope","metric","estimate","actual","deviation_pct","over20pct","status","md_path"])
    write_csv(ROOT / "experiments/dsp_composition.csv",composition,["id","series","Conv1_DSP","Conv2_DSP","Conv3_DSP","other_DSP","total_DSP","status"])
    write_csv(ROOT / "experiments/bursts.csv",bursts,["id","direction","bundle","inferred_words","word_bits","loop","note"])
    write_csv(ROOT / "experiments/conv3_comparison.csv",conv3,["id","variant","kernel_DSP","kernel_BRAM18K","kernel_LUT","kernel_FF","kernel_latency_cycles",
                                                           "padding_DSP","padding_BRAM18K","padding_LUT","padding_FF","border_mse","bit_exact","ii_ok"])
    print("Analyzed",len(structures),"runs;",len(estimates),"estimate comparisons")


if __name__ == "__main__":
    main()
