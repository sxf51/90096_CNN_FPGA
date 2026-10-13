#!/usr/bin/env python3
"""Remove an input reference mistakenly archived as a failed run's output."""
import json
from run_exp import ROOT, append_log

archive = ROOT / "experiments/E011_apfixed_w16a16"
config = json.loads((archive / "config.json").read_text())
if config.get("validation"):
    raise RuntimeError("This correction applies only to a run with no validation output")
(archive / "butterfly_output.bin").unlink(missing_ok=True)
append_log("E011 archive correction: removed copied numpy input reference; compile failed before producing any model output. Output archival now selects csim/build only.")
