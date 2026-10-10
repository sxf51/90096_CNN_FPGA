#!/usr/bin/env python3
"""Select the fastest three accepted frame points and preplan final verification."""
import argparse
import csv
import json
import math
import subprocess
import sys
from analyze_arch import eligible
from plan_arch import plan
from run_exp import ROOT, number, write_json

REQUIRED = ([f"G{i:02}" for i in range(1,4)] + [f"S{i:02}" for i in range(1,7)] +
            [f"P{i:02}" for i in range(1,9)] + ["P10","P11","P12"] +
            [f"W{i:02}" for i in range(1,10)] + [f"C{i:02}" for i in range(1,7)] +
            [f"F{i:02}" for i in range(1,20)] + ["W10","W11","W12","W13","C07","C08","C09",
                                                 "W14","W15","W16","C10","C11"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count",type=int,choices=(2,3),default=3)
    args = parser.parse_args()
    rows = list(csv.DictReader((ROOT / "experiments/results.csv").open(newline="")))
    missing = set(REQUIRED)-{row["id"] for row in rows}
    if missing:
        raise RuntimeError("Initial exploration still running: "+", ".join(sorted(missing)))
    accepted = []
    for row in rows:
        config = json.loads((ROOT / "experiments" / row["md_path"]).with_name("config.json").read_text())
        if eligible(row,config) and number(row["latency_ms_est"]) is not None:
            accepted.append(row)
    def rank(row):
        config = json.loads((ROOT / "exp/configs" / (row["id"]+".json")).read_text())
        flags = config.get("defines", {})
        online = flags.get("EXP_ONLINE_PAD",flags.get("EXP_ALL_CONTINUOUS",0))
        return (number(row["latency_ms_est"]),not bool(online),number(row["LUT"]),number(row["BRAM18K"]))
    accepted.sort(key=rank)
    selected = accepted[:args.count]
    if len(selected) < 2:
        raise RuntimeError("Fewer than two accepted frame points")
    todo = []
    for index,row in enumerate(selected):
        archive = ROOT / "experiments" / row["md_path"].split("/")[0]
        archived = json.loads((archive / "config.json").read_text())
        base = json.loads((ROOT / "exp/configs" / (row["id"]+".json")).read_text())
        estimates = {"DSP":number(row["DSP"]), "BRAM18K":number(row["BRAM18K"]),
                     "URAM":number(row["URAM"]), "LUT":number(row["LUT"]),
                     "T":number(row["T_target"]), "latency_cycles":number(row["latency_cycles"]),
                     "basis":"Frozen parent "+row["id"]+" HLS estimates. Implementation resources may optimize/change, RTL finite-FIFO latency may differ. No board performance estimate is substituted for actual reports."}
        first = 80+3*index
        validation_id = f"F{first}"
        validation = {**base,"id":validation_id,"name":"final_all_supplied_"+row["id"],
                      "stage":"arch_final", "series":"F", "scope":"frame", "csim_only":True,
                      "set14":True,"defines":{**base.get("defines",{}),"EXP_FRAMES":2},
                      "estimates":estimates,
                      "purpose":"Validate selected point "+row["id"]+" on every supplied Set14 pair and two butterfly frames. Every output bit must match the independently real-ap_fixed-verified numpy reference, with unchanged normalized-float delta PSNR>=-0.1dB and six-pixel borders. Missing comic stays explicit.",
                      "changes":"Frozen selected design/defines; enable full supplied-image comparison only. No source algorithm change.",
                      "interpretation":"Full supplied-image equality establishes this architecture preserves the measured precision point on all supplied inputs. It does not establish the missing14th image, routed timing or RTL behavior.",
                      "conclusion":"Keep precision acceptance provisional until comic is available; compare independent implementation/cosim reports."}
        precision = row["precision_w_a_acc"]
        if precision == "w10a10acc23":
            validation["numpy_reference"] = "exp/numeric_reference/w10a10/numpy_reference"
        elif precision == "w10_8_10a10acc23_21_23":
            validation["numpy_reference"] = "exp/numeric_reference/mixed_conv2w8/numpy_reference"
        else:
            raise RuntimeError("No independently verified all-image reference for "+precision)
        validation.pop("quality_reference",None)
        cases = [validation]
        for offset,operation in ((1,"impl"),(2,"cosim")):
            exp_id = f"F{first+offset}"
            cases.append({"id":exp_id,"name":"final_"+operation+"_"+row["id"],"series":"F","stage":"arch_final","scope":"frame",
                          "operation":operation,"verify_parent":row["id"],"validation_parent":validation_id,"design":base["design"],
                          "clock":base["clock"],"settings":base["settings"],"timeout":21600 if operation == "cosim" else 10800,
                          "estimates":estimates,
                          "purpose":"Verify selected exact resource-feasible point "+row["id"]+" using "+operation+". " +
                                    ("Run two complete butterfly transactions with dataflow profiling and a six-hour process-tree timeout; compare real latency/interval to frozen HLS predictions and detect deadlock." if operation == "cosim" else "Run out-of-context Vivado placement/routing; report final WNS and physical resources independently of HLS estimates."),
                          "notes":"Selected globally by lowest HLS latency among resource-feasible exact frame records; full14-image acceptance remains unavailable."})
        for config in cases:
            plan(config)
            subprocess.run([sys.executable,str(ROOT / "exp/commit_exp.py"),config["id"],"plan_"+config["name"]],cwd=ROOT,check=True)
            todo.append(config["id"])
    write_json(ROOT / "experiments/final_selection.json",{
        "selection_method":"Globally lowest latency_ms_est accepted frame points from both phases; exact ties prefer online padding, then lower LUT/BRAM. Validation operations/PE/layer kernels excluded",
        "selected":[{key:row[key] for key in ("id","design","T_target","clock_target_ns","latency_ms_est","DSP","LUT","md_path")} for row in selected],
        "queue":todo,"missing_comic":True})
    print("Final queue:"," ".join(todo))


if __name__ == "__main__":
    main()
