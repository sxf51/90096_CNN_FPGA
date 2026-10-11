#!/usr/bin/env python3
"""Derive architecture comparison CSVs and report-based estimate audits."""
import csv
import json
import math
import re
from pathlib import Path
from run_exp import ROOT, markdown_table, number, resource_summary

SERIES_NOTES = {
    "S": "Whole-network DATAFLOW overlaps the dedicated layer engines. Tile fusion removes full feature maps but executes Conv1/Conv2 and Conv3 sequentially, recomputes halos, and can lose memory parallelism. Requested AXI burst limits are upper bounds; only inferred bursts are evidence of burst generation. DDR payload/bandwidth models exclude protocol stalls and are lower bounds.",
    "G": "Scatter trades the channel-wide gather line/window storage for five32-bit partial rows and a5x5 register window. Explicit padding retains a32-channel row; merged edge kernels remove it but introduce nine coefficient classes, wider coefficients, selection and runtime merge work. Equality of every butterfly output, including six-pixel borders and the repeated frame, is the padding gate.",
    "P": "Two INT8 products share one DSP only when operand packing and signed-low borrowing are handled explicitly. Exact ten-bit coefficient residuals add fabric control/adders, and adjacent-pixel Conv3 needs a5x6 window plus odd-column disposal. Complete INT16 products require separately counted limb multipliers or overlapping-field fabric recovery; compare P13-P16's matched controls. Extra multiplier/pipeline depth is paid on every pixel in nested fold schedules. PE cycle counts cannot be interpreted as network-frame times.",
    "W": "Integer G2 preserves exact products and performs an exact divide-by-four before the original layer cast. Wider transforms and inverse additions, nine subkernels, runtime weight transforms and two raster row FIFOs are outside a multiplication-only budget. The128x128 tile grid computes65536 output positions before discarding the511 extra positions. PE/layer results do not establish full-network feasibility.",
    "C": "The combination retains Winograd Conv1 and uses packing only on other layers, avoiding incompatible transformed INT8 operands. Multiplier budgets omit residual/borrow correction, inverse arithmetic, runtime transformed weights and raster reorder. Dedicated layer resource counts must be summed once; nested child reports repeat their parents' resources.",
    "F": "Continuous scheduling separates window generation and MAC folds, shifts channel registers and explicitly registers fabric reduction trees. This can remove pixel fill/drain but costs pipeline registers and wide window FIFOs. Online padding overlaps source reads with padded writes; old row serialization can create finite-FIFO stalls absent from maximum-component HLS estimates. RTL cycles and routed slack remain the final evidence.",
}
MODULE_CONTROLS = {
    "F15": ("F14", ("engine1", "conv2_stream", "engine3")),
    "W17": ("W14", ("transform_weights",)),
    "W18": ("W15", ("transform_weights",)),
    "F24": ("F23", ("srcnn_Pipeline_load1", "srcnn_Pipeline_load1_channels_load1_rows_load1")),
    "F25": ("F24", ("srcnn_Pipeline_load1", "srcnn_Pipeline_load1_channels_load1_rows_load1",
                     "srcnn_Pipeline_load1_rows_load1")),
}


def write_csv(path, rows, columns):
    with path.open("w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def area_breakdown(report):
    columns = ["Name", "BRAM_18K", "DSP", "FF", "LUT", "URAM"]
    rows, active = [], False
    with report.open(newline="") as source:
        for cells in csv.reader(source, delimiter="|"):
            values = [cell.strip() for cell in cells[1:-1]]
            if values == columns:
                active = True
                continue
            if not active or len(values) != len(columns):
                continue
            category = values[0]
            if category in {"DSP", "Expression", "FIFO", "Instance", "Memory", "Multiplexer", "Register", "Total"}:
                rows.append({"category": category, **{key: number(value)
                             for key, value in zip(columns[1:], values[1:])}})
                if category == "Total":
                    return rows
    raise RuntimeError("Missing HLS utilization summary: " + str(report))


def scope(config, row):
    if config.get("operation"):
        return config.get("scope", "frame")
    if config.get("scope") in {"PE", "layer", "frame"}:
        return config["scope"]
    if config.get("tb_files") == ["exp/tb/integer_numeric.cpp"]:
        return "PE"
    if "micro" in row["design"]:
        return "PE"
    return "frame"


def eligible(row, config):
    return (scope(config,row) == "frame" and not config.get("operation") and
            row["status"] in {"pass", "provisional"} and str(row["csim_pass"]).lower() == "true" and
            (not config.get("fixed") or
             (str(row["bit_exact"]).lower() == "true" and number(row["delta_psnr"]) is not None and
              number(row["delta_psnr"]) >= -.1)))


def actual_measurement(row, config, key):
    operation = config.get("operation")
    verification = config.get("verification", {})
    if operation == "cosim":
        return number(verification.get("rtl_latency_max")) if key == "latency_cycles" else None
    if operation == "impl":
        if key == "latency_cycles":
            return None
        if key == "BRAM18K":
            tiles = number(verification.get("impl_BRAM36"))
            return 2*tiles if tiles is not None else None
        return number(verification.get("impl_"+key))
    return number(row.get(key))


def failure_reason(row, archive):
    cancellation = archive / "cancellation.json"
    if cancellation.is_file():
        record = json.loads(cancellation.read_text())
        return "User-priority cancellation (" + record["signal"] + "): " + record["reason"] + " No RTL verdict or measured cycles."
    if row["status"] in {"pass", "provisional", "csim_pass", "impl_complete", "cosim_complete", "analysis_complete"}:
        return ""
    if row["status"] == "infeasible":
        from run_exp import CAPACITY, LIMIT
        excess = [f"{key}={row[key]} exceeds {CAPACITY[key]*LIMIT[key]:g}"
                  for key in CAPACITY if number(row.get(key)) is not None and
                  number(row[key]) > CAPACITY[key]*LIMIT[key]]
        return "; ".join(excess)
    diagnostics = []
    oom = archive / "diagnostics/kernel_oom.txt"
    if oom.is_file() and "Out of memory:" in oom.read_text():
        diagnostics.append("Kernel-confirmed host OOM killed Vivado during synthesis; no routed timing/resource result")
    for name in ("csim.log.txt", "csynth.log.txt", "impl.log.txt", "cosim.log.txt"):
        path = archive / name
        if not path.is_file():
            continue
        lines = path.read_text(errors="replace").splitlines()
        if any("ap_fixed_base.h" in line and "error:" in line for line in lines) and any(
                "expanded from macro 'F2'" in line or "expanded from macro 'F3'" in line for line in lines):
            diagnostics.append("F2/F3 size macros collide with AMD ap_fixed header identifiers; independent header-order retries preserve the failed source")
        messages = [line.strip() for line in lines if
                    re.search(r"ERROR:|error:|EXP_TIMEOUT|deadlock detected", line, re.IGNORECASE)]
        diagnostics.extend(messages[:2])
    return "; ".join(dict.fromkeys(diagnostics)) or row["notes"]


def module_for(modules, layer):
    preferred = ("conv1_stream", "conv1_tiles", "wino_engine", "engine1") if layer == 1 else (
        ("conv2_stream", "engine2") if layer == 2 else ("conv3_stream", "engine3"))
    preferred += (f"tile_region_Pipeline_tile_c{layer}_fold",)
    for name in preferred:
        found = [module for module in modules if module["module"] == name]
        if found:
            return found[0]
    return None


def dsp_composition(row, config):
    if scope(config,row) != "frame" or config.get("operation"):
        return None
    parts = [module_for(config.get("parsed_modules", []),layer) for layer in (1,2,3)]
    counts = [number(part.get("DSP")) if part else None for part in parts]
    total = number(row.get("DSP"))
    if total is None or any(count is None for count in counts):
        return None
    remainder = total-sum(counts)
    if remainder < 0:
        raise RuntimeError("Overlapping module DSP accounting: "+row["id"])
    return {"id":row["id"], "series":row["series"] or "E",
            "Conv1_DSP":counts[0], "Conv2_DSP":counts[1], "Conv3_DSP":counts[2],
            "other_DSP":remainder, "total_DSP":total, "status":row["status"]}


def deviation_explanation(row, config, comparisons):
    deviations = [item for item in comparisons if item["over20pct"]]
    if not deviations:
        return ""
    modules = config.get("parsed_modules", [])
    loops = config.get("parsed_loops", [])
    folded = [loop for loop in loops if "fold" in loop.get("loop", "")]
    lines = []
    design = config.get("design", "")
    if config.get("operation") == "cosim":
        lines.append("RTL includes finite FIFO backpressure and AXI handshake stalls. The parent HLS report is a static component-bound estimate; compare the two recorded transactions and interval before attributing the difference to arithmetic II.")
    elif config.get("operation") == "impl":
        lines.append("Routed resource counts use the optimized physical netlist, while the frozen estimate is HLS operator/memory accounting. The routed timing and utilization reports are the evidence for this mapping difference, and do not measure frame cycles.")
    elif row["id"] == "S01":
        lines.append("The paper model assumed external scratch buffers. Neither required scratch AXI bundle was generated, so the report allocates both full feature arrays on chip. This is an invalid DDR configuration, which explains the memory-budget failure.")
    elif "tile_fusion" in design:
        lines.append("The paper projection counted MAC lanes and cache bits, but omitted dynamic clamped spatial-bank selection and address logic. The tile pipeline reports isolate the MAC counts; the top's remaining DSP count includes address/control arithmetic. Conv1/Conv2 folds restart for every scheduled halo feature, then Conv3 runs sequentially. Even at II1, each restart pays the reported iteration depth; the scheduled halo ratio is shown in the DDR/cache table. These observed costs explain the LUT and cycle excess, rather than an unexplained multiplier-count increase.")
        if row["id"] == "S05":
            lines.append("S05's tile_region_csynth.rpt reports33751 multiplexer LUT,7524 memory LUT and52475 instance LUT, totaling96251 LUT for tile_region alone. Its instance list includes nine32x34-bit address products at4DSP each plus3DSP float output scaling; these are outside the162/64/25 layer-MAC split. The complete top is120033 LUT, beyond81984.")
    elif "packing_network" in design or "combination" in design:
        lines.append("Packing preserves ten-bit precision by restoring signed-low8 coefficient residuals and correcting negative borrowing. Its one-DSP pair therefore still needs wider fabric arithmetic, selection and pipeline stages. The nested fold loops restart at every pixel/tile, charging their full iteration latency in addition to T; pure-MAC budgets omitted that drain cost. The reported layer LUTs and loop depths below quantify the excess. Uniform INT8 cannot remove this logic without failing the unchanged precision gate.")
    if "winograd" in design or "combination" in design:
        bound = next((module for module in modules if module["module"] == "conv1_tiles"),None)
        if bound:
            lines.append("The nested Conv1 tile producer reports "+str(bound.get("latency_cycles"))+" cycles. Its264x264 scan contains a conditional4*T fold, and the maximum bound charges that branch at every scanned coordinate; only128x128=16384 coordinates actually produce tiles. Consequently the reported worst-case bound is inflated, even with the requested fold II. W10-W13/C07 isolate this by replacing the nested branch with a fixed16384*(4*T) MAC loop. This is report-bound tightening until RTL cycles confirm an actual throughput change.")
        else:
            lines.append("Winograd budgets count2304 MACs per output but also need34-bit inverse additions,144 transformed values per window, a four-pixel output packet and two512-deep640-bit raster FIFOs. Continuous schedules eliminate tile restarts but retain this storage and transform logic; the layer/module table identifies whether the direct Conv2/Conv3 engine now sets the cycle bound.")
            if not config.get("operation") and scope(config,row) == "frame":
                t = number(config.get("T"))
                paper_cycles = number(config.get("estimates",{}).get("latency_cycles"))
                reported_cycles = number(row.get("latency_cycles"))
                if t is not None and paper_cycles is not None and reported_cycles is not None:
                    floor = 255*255*t
                    lines.append("The T-based compute floor is "+str(floor)+" cycles. The paper plan reserved "+
                                 str(paper_cycles-floor)+" additional cycles; the reported top bound has "+
                                 str(reported_cycles-floor)+" cycles above that floor. This compares the conservative load/startup/reorder allowance with the actual HLS bound; it is not a measured DDR or RTL stall count.")
                transform = next((module for module in modules if module["module"] == "transform_weights"),None)
                dataflow = next((module for module in modules if module["module"] == "dataflow_region"),None)
                if transform and dataflow:
                    loader_lut,inference_lut,total_lut = number(transform.get("LUT")),number(dataflow.get("LUT")),number(row.get("LUT"))
                    if all(value is not None for value in (loader_lut,inference_lut,total_lut)):
                        lines.append("Disjoint top-level report counts: transform_weights uses "+str(loader_lut)+
                                     " LUT and "+str(transform.get("FF"))+" FF; dataflow_region uses "+
                                     str(inference_lut)+" LUT. The remaining "+str(total_lut-loader_lut-inference_lut)+
                                     " top-level LUT cover memories, interfaces, loading and control outside those functions. Runtime raw/transformed coefficient banks and their selectors remain required by the float-weight input contract, and are not represented by a DSP-only MAC budget. Nested children are not added again.")
    elif "continuous_direct" in design or "continuous_rotate" in design or "continuous_ieee" in design or "fifo_lutram" in design or "uram_line" in design:
        lines.append("The paper cache estimate used stored-bit capacity, whereas channel/row banking and shallow-wide FIFO mapping consume whole memory primitives. Explicit LUTRAM and URAM bindings change that granularity. Registered reductions add pipeline FF and address/window FIFOs while continuous loops remove per-pixel drain; compare the memory counts and folded iteration depths to the storage controls. HLS maximum-component cycles still exclude finite-FIFO stalls, especially with old row-serialized padding.")
        online = next((module for module in modules if module["module"] == "online_pad_pixel2_2_s"), None)
        if online:
            bits = 32 * config.get("defines", {}).get("EXP_A_BITS", 10)
            lines.append("The online Conv3 pad row is explicitly aggregated into " + str(bits) + "-bit words and its parsed module uses " + str(online["BRAM18K"]) + " BRAM18K. This packs channel fields into wide memory ports, whereas F08's old pad control leaves individual channel fields in separate banks. That storage-fragmentation change explains the BRAM saving independently of the Conv3 rotation or MAC count.")
    elif scope(config,row) == "PE":
        if "packing_int16_pe" in design:
            mode = config.get("defines", {}).get("EXP_PACK16_MODE")
            explanation = {
                0: "Two independent complete16x16 DSP products need no limb/overlap repair; this is the matched array/control baseline.",
                1: "Byte splitting requires four packed product groups (low-low, high-low, low-high and high-high), then two full32-bit recombinations. Unsigned low limbs need nine signed operand bits. This recovers every bit but does not reduce DSP versus the two-product baseline.",
                2: "The27x16 DSP product carries overlapping fields. Two fabric products (8x16 low term and9x16 residual) recover both complete32-bit outputs, plus a43/44-bit subtraction and widened recombination. HLS can prune unused high bits and pipeline/carry logic; the one-DSP count does not mean that all multiplication moved into one DSP.",
                3: "One complete16x16 product is bound to DSP and the other to fabric. Fabric LUT/carry/register mapping depends on operand width and clock; it is the matched control for overlapping-field repair, not a packed primitive.",
            }
            lines.append(explanation.get(mode, "Compare complete INT16 products with the matched direct and mixed controls."))
            lines.append("LUT/FF paper budgets reserve mapping and pipeline margin. Parsed top DSP/LUT/FF, actual clock and pack16_terms iteration depth quantify the actual cost; no whole-network frame speedup is inferred from these64-term PE calls.")
            if mode in {0, 3}:
                lines.append("The matched direct controls export their arrays as ap_memory ports instead of allocating internal input/output memories. Their multiplier instances report zero external FF, leaving only loop/control registers. The paper FF allowance assumed additional external datapath stages, so it overestimates the implemented single-cycle operator schedule. Expression and Multiplexer rows account for the remaining control LUT; the mixed control's Instance row also includes its fabric multiplier.")
            else:
                lines.append("The Instance row separates byte/fabric multiplier LUT from the Expression row's recombination and correction arithmetic. Register counts cover the external values delayed across the longer operator schedule; DSP internal pipeline registers are not counted as fabric FF. Widened C++ arithmetic does not force every high bit or delayed temporary to survive synthesis. The paper FF allowance reserved complete intermediate stages, whereas the report counts only the retained external stages, explaining the unused FF margin.")
        elif "ieee_decode" in design:
            lines.append("Converter planning allowances reserved selection/control margin. Exact IEEE construction operates on a ten-bit magnitude and highest-set-bit selector, then assigns binary32 exponent/significand fields; its finite range lets synthesis remove unused selector states and registers. The legacy control retains integer-to-float and float scaling operators. These PE array-memory ports also omit the full network's AXI address/handshake logic, so PE resource differences cannot be subtracted blindly from a frame estimate. Compare the parsed DSP, loop depth and clock before integrating the exact converter.")
        else:
            lines.append("PE LUT estimates were planning allowances, not bit-level netlists. Direct control avoids transform/borrow logic; wider Winograd operands increase transform/inverse fabric width; exact10 packing adds residual repair. The measured DSP count and loop II must be evaluated independently of unused LUT margin.")
    if folded:
        lines.append("Observed fold depth/II: "+"; ".join(loop["loop"]+" depth="+str(loop.get("IterationLatency",loop.get("PipelineDepth")))+", II="+str(loop.get("actual_ii")) for loop in folded)+".")
    return "\n\nExplicit explanation of deviations above20%:\n\n"+"\n\n".join(lines)+"\n"


def main():
    rows = list(csv.DictReader((ROOT / "experiments/results.csv").open(newline="")))
    structures, estimates, composition, bursts, conv3, warnings, int16, int16_area = [], [], [], [], [], [], [], []
    for row in rows:
        archive = ROOT / "experiments" / Path(row["md_path"]).parent
        path = archive / "config.json"
        if not path.is_file():
            continue
        config = json.loads(path.read_text())
        pe_area = []
        if config.get("design") == "designs/packing_int16_pe":
            int16.append({**row, **config.get("validation", {}),
                          "mode":config.get("defines", {}).get("EXP_PACK16_MODE")})
            if (archive / "csynth.rpt").is_file():
                pe_area = area_breakdown(archive / "csynth.rpt")
                int16_area.extend({"id": row["id"], **item} for item in pe_area)
        derived = {**row, "scope": scope(config,row), "operation": config.get("operation", ""),
                   "validation_only": bool(config.get("csim_only") and config.get("set14")),
                   "eligible_provisional": eligible(row,config),
                   "failure_reason": failure_reason(row,archive),
                   "ddr_bytes_per_frame": config.get("ddr_bytes_per_frame", ""),
                   "feature_recompute_ratio": config.get("feature_recompute_ratio", ""),
                   "cache_bits": config.get("cache_bits", ""),
                   "inferred_image_read_bursts": "", "inferred_image_write_bursts": ""}
        logs = archive / "csynth.log.txt"
        dataflow_warnings = []
        if logs.is_file():
            log_text = logs.read_text()
            dataflow_warnings = list(dict.fromkeys(line.strip() for line in log_text.splitlines() if
                "WARNING: [HLS " in line and re.search(r"dataflow|FIFO|deadlock", line, re.IGNORECASE)))
            warnings.extend({"id":row["id"],"series":row["series"] or "E","warning":message,
                             "source":"csynth.log.txt","md_path":row["md_path"]}
                            for message in dataflow_warnings)
            observed = re.findall(r"burst (reads|writes) of length (\d+) and bit width (\d+) in loop '([^']+)'[^\n]*?on bundle '([^']+)'",log_text)
            for direction, count, bits, loop, bundle in observed:
                bursts.append({"id": row["id"], "direction": direction, "bundle": bundle,
                               "inferred_words": count, "word_bits": bits, "loop": loop,
                               "note": "Inference length may be partitioned by AXI max burst settings"})
            for direction, key in (("reads","inferred_image_read_bursts"),("writes","inferred_image_write_bursts")):
                counts = sorted({int(count) for kind,count,_,_,bundle in observed if kind == direction and bundle in {"image_in","image_out"}})
                derived[key] = "/".join(map(str,counts)) if counts else "none reported"
        derived["dataflow_warning_count"] = len(dataflow_warnings)
        bandwidth = config.get("ddr_lower_bound_ms", [])
        derived["ddr_theoretical_lower_bound_ms"] = bandwidth[0] if bandwidth else ""
        derived["ddr_50pct_lower_bound_ms"] = bandwidth[1] if bandwidth else ""
        structures.append(derived)
        layer_counts = dsp_composition(row,config)
        if layer_counts:
            composition.append(layer_counts)
        if not row["series"]:
            continue
        comparisons = []
        for key in ("DSP", "BRAM18K", "URAM", "LUT", "FF", "latency_cycles"):
            paper = number(config.get("estimates",{}).get(key))
            actual = actual_measurement(row,config,key)
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
        reproduction_start = text.index("## 4. Reproduction / 复现\n\n")
        reproduction_end = text.index("## 5. Results / 结果", reproduction_start)
        original = "python3 exp/run_exp.py --config exp/configs/" + row["id"] + ".json"
        section = "## 4. Reproduction / 复现\n\n```sh\npython3 exp/reproduce_exp.py " + row["id"] + " --run\n```\n\nAllocates a fresh ID and restores frozen design/testbench sources; verification also rebuilds its parent. See [reproduction guide](../REPRODUCE.md). Original reserved invocation:\n\n```sh\n" + original + "\n```\n\n"
        text = text[:reproduction_start] + section + text[reproduction_end:]
        text = re.sub(r"\n<!-- AUTO: resource percentages -->.*?<!-- END: resource percentages -->\n", "", text, flags=re.S)
        result_end = text.index("## 6. Interpretation / 解读")
        summary = "<!-- AUTO: resource percentages -->\n\n" + resource_summary(row) + "\n<!-- END: resource percentages -->\n\n"
        text = text[:result_end] + summary + text[result_end:]
        narrative = archive / "interpretation.md"
        human = (narrative.read_text().strip() if narrative.is_file() else config.get("interpretation", ""))
        human += "\n\n"+SERIES_NOTES.get(row["series"], "")
        if config.get("operation") == "cosim":
            measured = config.get("verification", {})
            if measured.get("rtl_status") == "Pass":
                human += ("\n\nBoth RTL transactions pass. Maximum latency is "+str(measured.get("rtl_latency_max"))+
                          " cycles and interval is "+str(measured.get("rtl_interval_max"))+" cycles; latency differs from the frozen HLS bound by "+
                          str(measured.get("cycle_deviation_pct"))+"%. Finite-FIFO/AXI handshake costs are included in RTL. "
                          "This ideal-clock simulation does not establish routed timing or board latency.")
            if config.get("verification_profiles"):
                human += ("\n\nThe archived profiling/channels.csv and processes.csv locate FIFO backpressure and per-process stalls. "
                          "Fast source/window producers are expected to block behind the T-fold MAC consumer; a large write-block fraction alone is not evidence that deeper FIFOs would improve frame throughput. "
                          "Process counters span both transactions and include startup/inactive cycles; overlapping stalls cannot be summed to explain the complete latency difference.")
            if config.get("profiling_archive_error"):
                human += "\n\nRTL counter archive unavailable: "+config["profiling_archive_error"]
        human += "\n\nEstimate audit (parsed values; zero estimates have no percentage denominator):\n\n"
        human += markdown_table(comparisons,["metric","estimate","actual","deviation_pct","over20pct"])
        human += deviation_explanation(row,config,comparisons)
        if pe_area:
            human += "\nUtilization categories parsed from csynth.rpt; Total is not added to its component rows:\n\n"
            human += markdown_table(pe_area, ["category", "DSP", "LUT", "FF", "BRAM_18K", "URAM"])
        if report_rows:
            human += "\nWhole layer evidence from csynth XML (child pipeline reports are not added again):\n\n"
            human += markdown_table(report_rows,["module","latency_cycles","DSP","BRAM18K","LUT","FF"])
        if row["id"] in MODULE_CONTROLS:
            parent_id, names = MODULE_CONTROLS[row["id"]]
            control_path = next((ROOT / "experiments").glob(parent_id+"_*/config.json"), None)
            if control_path:
                control = json.loads(control_path.read_text())
                comparison = []
                for exp_id, data in ((parent_id, control), (row["id"], config)):
                    comparison.extend({"id":exp_id, **module} for module in data.get("parsed_modules", [])
                                      if module["module"] in names)
                human += "\nMeasured control-module comparison (identical precision and T):\n\n"
                human += markdown_table(comparison,["id","module","clock_est_ns","latency_cycles","DSP","BRAM18K","LUT","FF"])
                if row["id"] == "F15":
                    human += "\nLatency0 removes registers from the reduction stages. The measured FF saving accompanies a larger LUT count, so register removal alone does not make T8 feasible. Compare the three engines to locate the saving; the output converter can still set the top estimated clock.\n"
                elif row["id"] in {"W17", "W18"}:
                    human += "\nOnly the raw coefficients' output-channel partition changes in this pair; transformed MAC banks remain fixed. Deeper raw banks change the inferred RAM/register and selector mapping in the sequential loader. Compare the loader saving with the total remaining LUT excess before projecting another feasible point.\n"
                else:
                    human += "\nOnly the Conv1 loader organization changes in this control pair. F24's report removes the quotient-address multiplier but identifies the flattened kx counter's compare/and/select/add/store path as the new clock limit. F25 tests an unflattened inner loop; its counter clock must be weighed against repeated pipeline drain. The inference engines, coefficient precision and runtime parameter contract remain identical.\n"
        if loops:
            human += "\nPipeline depth and II evidence; nested pixel schedules pay the reported iteration latency at every restart:\n\n"
            human += markdown_table(loops,["module","loop","IterationLatency","PipelineDepth","actual_ii","target_ii","ii_ok"])
        if config.get("errors"):
            human += "\nObserved errors: "+"; ".join(config["errors"])+"\n"
        if derived["failure_reason"]:
            human += "\nArchived failure evidence: "+derived["failure_reason"]+"\n"
        if dataflow_warnings:
            human += "\nDATAFLOW scheduling warnings parsed from csynth.log.txt:\n\n"
            human += markdown_table([{"warning":message} for message in dataflow_warnings],["warning"])
            human += "\nCaller inputs are read-only weights loaded before DATAFLOW; their start synchronization may limit overlap. C simulation uses unbounded software streams, so only finite-FIFO RTL profiling can establish the resulting throughput and absence of deadlock.\n"
        if config.get("primitive_probe"):
            probe = config["primitive_probe"]
            human += "\nRouted DSP48E2 inspection (dsp_primitives.csv):\n\n"+markdown_table([probe],[
                "completed","DSP48E2_cells","pre_adder_used","error"])
            cells = [{"cell":cell,**properties} for cell,properties in probe.get("cells",{}).items()]
            human += "\n"+markdown_table(cells,["cell","AMULTSEL","PREADDINSEL","AREG","BREG","DREG","ADREG","MREG","PREG","INMODEREG"])
        if row["id"] == "S01":
            human += "\nThe global arrays remained on chip because scratch1/scratch2 AXI bundles were absent. Consequently the reported memory/cycles describe an invalid on-chip probe, not an implemented DDR design. The zero external-memory BRAM assumption failed because the interface pragma was ignored. Changing the frozen top signature needs human decision.\n"
        if row["id"] == "C10":
            controls = {point["id"]:point for point in rows if point["id"] in {"W14","W17"}}
            if len(controls) == 2:
                from run_exp import CAPACITY, LIMIT
                saving = number(controls["W14"]["LUT"])-number(controls["W17"]["LUT"])
                projected = number(row["LUT"])-saving
                human += ("\nUnimplemented raw-bank follow-up projection: transferring the measured W14-to-W17 total saving of "+
                          str(saving)+" LUT to C10 would leave approximately "+str(projected)+
                          " LUT, above the unchanged "+str(CAPACITY["LUT"]*LIMIT["LUT"])+
                          " gate. This projection is not hardware evidence and does not establish feasibility; retain C10's actual failure and finish the remaining controls.\n")
        if config.get("ddr_bytes_per_frame"):
            human += "\nDDR/burst model from configuration and synthesis logs:\n\n"+markdown_table([derived],[
                "ddr_bytes_per_frame","feature_recompute_ratio","cache_bits", "inferred_image_read_bursts",
                "inferred_image_write_bursts","ddr_theoretical_lower_bound_ms","ddr_50pct_lower_bound_ms"])
        start = text.index("## 6. Interpretation / 解读\n\n")+len("## 6. Interpretation / 解读\n\n")
        end = text.index("\n## 7. Conclusion",start)
        md_path.write_text(text[:start]+human.rstrip()+"\n"+text[end:])
    extra = ["scope","operation","validation_only","eligible_provisional","failure_reason","dataflow_warning_count","ddr_bytes_per_frame","feature_recompute_ratio","cache_bits",
             "inferred_image_read_bursts","inferred_image_write_bursts","ddr_theoretical_lower_bound_ms","ddr_50pct_lower_bound_ms"]
    write_csv(ROOT / "experiments/architecture_data.csv",structures,list(rows[0])+extra)
    write_csv(ROOT / "experiments/estimate_actual.csv",estimates,["id","series","scope","metric","estimate","actual","deviation_pct","over20pct","status","md_path"])
    write_csv(ROOT / "experiments/dsp_composition.csv",composition,["id","series","Conv1_DSP","Conv2_DSP","Conv3_DSP","other_DSP","total_DSP","status"])
    write_csv(ROOT / "experiments/bursts.csv",bursts,["id","direction","bundle","inferred_words","word_bits","loop","note"])
    write_csv(ROOT / "experiments/conv3_comparison.csv",conv3,["id","variant","kernel_DSP","kernel_BRAM18K","kernel_LUT","kernel_FF","kernel_latency_cycles",
                                                           "padding_DSP","padding_BRAM18K","padding_LUT","padding_FF","border_mse","bit_exact","ii_ok"])
    write_csv(ROOT / "experiments/dataflow_warnings.csv",warnings,["id","series","warning","source","md_path"])
    write_csv(ROOT / "experiments/int16_packing_comparison.csv",int16,[
        "id","mode","precision_w_a_acc","DSP","LUT","FF","BRAM18K","URAM",
        "clock_target_ns","clock_est_ns","latency_cycles","interval_cycles","ii_ok",
        "csim_pass","bit_exact","tested_terms","checked_products","boundary_triples",
        "role_sweep_triples","random_triples","signed16_value_coverage_per_role",
        "exhaustive_triples","status","md_path"])
    write_csv(ROOT / "experiments/int16_area_breakdown.csv", int16_area,
              ["id", "category", "DSP", "LUT", "FF", "BRAM_18K", "URAM"])
    print("Analyzed",len(structures),"runs;",len(estimates),"estimate comparisons")


if __name__ == "__main__":
    main()
