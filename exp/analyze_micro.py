#!/usr/bin/env python3
"""Derive PE mapping observations from archived synthesis reports."""
import csv
import json
import re
from run_exp import ROOT, markdown_table


def main():
    rows = []
    for exp_id in ("E051", "E052", "E053", "E054", "E055"):
        archive = next((ROOT / "experiments").glob(exp_id + "_*"))
        metrics = json.loads((archive / "metrics.json").read_text())
        config = json.loads((archive / "config.json").read_text())
        report = (archive / "csynth.rpt").read_text()
        operators = []
        for line in report.splitlines():
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            if len(cells) == 7 and cells[0].startswith("mul_") and cells[2].isdigit():
                operators.append({"instance": cells[0], "module": cells[1],
                                  "DSP": int(cells[3]), "FF": int(cells[4]), "LUT": int(cells[5])})
        row = {key: metrics[key] for key in ("id", "DSP", "LUT", "FF", "latency_cycles", "interval_cycles", "ii_ok")}
        row.update(scope="PE", tested_pairs=config["validation"]["tested_pairs"],
                   operator_DSP=sum(op["DSP"] for op in operators),
                   operator_LUT=sum(op["LUT"] for op in operators),
                   operator_FF=sum(op["FF"] for op in operators))
        rows.append(row)
        if exp_id in {"E051", "E054"}:
            interpretation = (f"The signed 16x16 multiply maps to {row['operator_DSP']} DSP in the Instance table. "
                f"The {config['clock']} ns target achieves {metrics['clock_est_ns']} ns estimated clock and samples II=1. "
                f"The complete 64-sample kernel uses {row['LUT']} LUT/{row['FF']} FF, with {row['latency_cycles']} cycles "
                f"and interval {row['interval_cycles']}; these are PE-kernel measurements, not frame latency. "
                f"C simulation verified {row['tested_pairs']} deterministic random signed16 pairs.")
            conclusion = "One DSP per scheduled signed16 multiply is supported at both tested clocks. Preserve this baseline for packing and Winograd PEs."
        elif exp_id == "E052":
            subtractors = len(re.findall(r"\|product_\w+\s*\|\s*-\|\s*0\|\s*0\|\s*31\|", report))
            interpretation = (f"Full unrolling maps {row['operator_DSP']} of 64 constant multipliers to DSPs, with "
                f"{row['LUT']} LUT and zero FF. The Expression table contains {subtractors} 31-LUT subtractors; "
                "the source repeats -127 four times, consistent with shift/subtract realization of that coefficient. "
                "Constant folding therefore does not generally remove DSPs for these non-power-of-two coefficients. "
                "Worst-case latency is legitimately zero for this combinational top; interval is one. "
                "The parser now accepts zero-cycle reports after all resource and numerical checks.")
            conclusion = "Do not budget all constant-weight products as LUT multipliers. Measure each coefficient family and use explicit fabric binding when needed."
        elif exp_id == "E053":
            interpretation = (f"BIND_OP fabric gives zero DSP. The actual mul_8s_8s_16_1_1 instance costs "
                f"{row['operator_LUT']} LUT and {row['operator_FF']} FF; complete kernel cost is {row['LUT']} LUT/{row['FF']} FF. "
                "The remaining 57 LUT are loop expressions/multiplexers. All 65,536 signed8 operand pairs pass, samples II=1. "
                "E055's same-loop add control costs 73 LUT, so replacing its 16-LUT adder gives a net 46-LUT increase. "
                "That difference is not the standalone multiplier cost; use the 62-LUT Instance evidence for budgets.")
            conclusion = "A single 8-bit fabric multiplier costs 62 estimated operator LUT in this kernel. Extrapolations must also include reductions, banks, control and timing."
        else:
            interpretation = (f"Same-loop add control uses {row['LUT']} LUT/{row['FF']} FF with II=1 and zero DSP. "
                "The Expression table attributes 16 LUT to the signed8 addition; the common controller costs 57 LUT. "
                "E053's net increment is 46 LUT, while its multiplier operator itself costs 62 LUT. "
                "Both kernels verify all signed8 operand pairs and report 66 cycles for 64 samples.")
            conclusion = "Use the control to distinguish shared kernel overhead from arithmetic operator cost."
        path = archive / (exp_id + ".md")
        text = path.read_text()
        start, end = text.index("## 6."), text.index("## 8.")
        replacement = "## 6. Interpretation / 解读\n\n" + interpretation + "\n\n"
        if operators:
            replacement += "Parsed operator evidence:\n\n" + markdown_table(operators, ["instance", "module", "DSP", "LUT", "FF"]) + "\n"
        replacement += "## 7. Conclusion and next step / 结论与下一步\n\n" + conclusion + "\n\n"
        path.write_text(text[:start] + replacement + text[end:])
    with (ROOT / "experiments/micro_mapping.csv").open("w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
