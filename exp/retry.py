#!/usr/bin/env python3
"""Generate a new immutable experiment ID for a corrected tool invocation."""
import argparse
import json
from run_exp import ROOT, write_json

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("source")
parser.add_argument("destination")
args = parser.parse_args()
config = json.loads((ROOT / f"exp/configs/{args.source}.json").read_text())
path = ROOT / f"exp/configs/{args.destination}.json"
if path.exists():
    raise RuntimeError("Refuse to overwrite " + str(path))
config.update(id=args.destination, name=config["name"] + "_retry")
config["changes"] += f" Retry of {args.source} with corrected runner flag serialization."
write_json(path, config)
