#!/usr/bin/env python3
"""Continue phase-one coordinate rounds from measured completed T scans."""
import csv
import json
import subprocess
import sys
import time
from run_exp import ROOT, append_log, lock, number, utc, write_json


def measured():
    with lock(ROOT/"workspace/exp_runs/.results.lock", wait_timeout=120):
        return list(csv.DictReader((ROOT/"experiments/results.csv").open(newline="")))


def choose(rows):
    eligible = [r for r in rows if number(r["latency_ms_est"]) is not None and r["csim_pass"] == "True"]
    accepted = [r for r in eligible if r["status"] in {"pass", "provisional"}]
    choices = accepted or eligible
    if not choices:
        raise RuntimeError("No completed numerically accepted control")
    return min(choices, key=lambda r: float(r["latency_ms_est"]))


def update(message):
    path = ROOT/"experiments/PROGRESS.md"
    text = path.read_text().split("\n## Coordinate controller\n")[0]
    path.write_text(text+"\n## Coordinate controller\n\n"+utc()+": "+message+"\n")
    print("COORDINATE", message, flush=True)


def execute(exp_id):
    update("Running "+exp_id+"; preceding completed measurements remain archived.")
    subprocess.run([sys.executable, str(ROOT/"exp/remote_exp.py"), str(ROOT/f"exp/configs/{exp_id}.json")], cwd=ROOT)


def prepare_storage(base, exp_id, storage):
    config = {**base, "id": exp_id, "name": f"storage_{storage}_T{base['T']}",
              "defines": {**base["defines"], "EXP_STORAGE": storage},
              "storage": ("register", "lutram", "bram")[storage],
              "purpose": f"Measure weight storage control at selected T={base['T']} with "
                         f"ideal DSP {8032/base['T']:g} and frame compute floor {65025*base['T']} cycles. "
                         "BRAM banking may waste capacity through many shallow memories; record actual resource excess.",
              "changes": "Same exact selected integer design and unroll split; only weight storage changes."}
    path = ROOT/f"exp/configs/{exp_id}.json"
    if path.exists():
        raise RuntimeError("Existing coordinate config")
    write_json(path, config)


def main():
    implementation = None
    update("Waiting for E057/E058/E059 banked T scans; synthesis is serialized by the memory lock.")
    while True:
        rows = measured()
        t_rows = [r for r in rows if r["id"] in {"E057", "E058", "E059"}]
        accepted = [r for r in rows if str(r["stage"]) == "4" and
                    r["design"].startswith("designs/dataflow") and
                    r["status"] in {"pass", "provisional"}]
        if accepted and implementation is None:
            parent = choose(accepted)
            config = {"id": "E070", "name": "first_feasible_implementation", "stage": 6,
                      "operation": "impl", "verify_parent": parent["id"], "clock": float(parent["clock_target_ns"]),
                      "design": parent["design"], "settings": "/home/lipuze/amdfpga/2026.1/Vitis/settings64.sh",
                      "purpose": "Run actual Vivado synthesis, placement and routing on the first measured "
                                 "resource-feasible supplied-image candidate while other coordinate studies continue. "
                                 "Missing comic keeps full-Set14 acceptance provisional."}
            write_json(ROOT/"exp/configs/E070.json", config)
            implementation = subprocess.Popen([sys.executable, str(ROOT/"exp/remote_exp.py"), str(ROOT/"exp/configs/E070.json")], cwd=ROOT)
            update("Started background implementation of "+parent["id"]+" as E070; no timing result inferred.")
        if len(t_rows) == 3:
            break
        time.sleep(5)
    best = choose(t_rows)
    update("T round completed; select "+best["id"]+" with measured status "+best["status"]+".")
    subprocess.run([sys.executable, str(ROOT/"exp/analyze_streaming.py")], check=True)
    subprocess.run([str(ROOT/"workspace/exp_runs/_tools/venv/bin/python"), str(ROOT/"exp/plots/overview.py")], check=True)
    subprocess.run([sys.executable, str(ROOT/"exp/prepare_scan.py"), "split", "--T", best["T_target"], "--base", f"exp/configs/{best['id']}.json"], check=True)
    for exp_id in ("E036", "E037", "E038"):
        execute(exp_id)
    candidates = [r for r in measured() if r["id"] in {best["id"], "E036", "E037", "E038"}]
    best = choose(candidates)
    base = json.loads((ROOT/f"exp/configs/{best['id']}.json").read_text())
    update("Split round completed; storage controls use "+best["id"]+".")
    for exp_id, storage in (("E064", 0), ("E067", 2)):
        prepare_storage(base, exp_id, storage)
        execute(exp_id)
    candidates = [r for r in measured() if r["id"] in {best["id"], "E064", "E067"}]
    best = choose(candidates)
    update("Storage round completed; clock round uses "+best["id"]+".")
    subprocess.run([sys.executable, str(ROOT/"exp/analyze_streaming.py")], check=True)
    subprocess.run([str(ROOT/"workspace/exp_runs/_tools/venv/bin/python"), str(ROOT/"exp/plots/overview.py")], check=True)
    subprocess.run([sys.executable, str(ROOT/"exp/prepare_scan.py"), "clock", "--T", best["T_target"], "--base", f"exp/configs/{best['id']}.json"], check=True)
    for exp_id in ("E041", "E042", "E043"):
        execute(exp_id)
    required = {"E039", "E040", "E045", "E048", "E063"}
    while not required <= {r["id"] for r in measured()}:
        time.sleep(5)
    update("All coordinate rounds completed; pending optional queues, candidate Set14 validation and first-phase finalization.")
    if implementation is not None:
        implementation.wait()
    subprocess.run([sys.executable, str(ROOT/"exp/summarize_phase1.py")], check=True)


if __name__ == "__main__":
    main()
