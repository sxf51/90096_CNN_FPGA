#!/usr/bin/env python3
"""Archive equivalent offline G2 tensors without changing runtime parameters."""
import csv
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from run_exp import ROOT, check_protected


def main():
    check_protected()
    source = ROOT / "src/weights/conv1_weights_3x_flp.bin"
    values = np.fromfile(source,dtype="<f4").reshape(64,9,9)
    raw = np.clip(np.rint(values.astype(np.float64)*512),-512,511).astype(np.int64)
    g2 = np.array([[2,0,0],[1,1,1],[1,-1,1],[0,0,2]],dtype=np.int64)
    transformed = np.empty((64,9,4,4),dtype=np.int64)
    for oc in range(64):
        for group in range(9):
            y,x = (group//3)*3,(group%3)*3
            transformed[oc,group] = g2 @ raw[oc,y:y+3,x:x+3] @ g2.T
    if np.max(np.abs(transformed)) >= 8192:
        raise RuntimeError("Transformed coefficient exceeds signed14 carrier")
    for path in sorted((ROOT / "experiments").glob("[WC]*_*/config.json")):
        archive = path.parent
        config = json.loads(path.read_text())
        if not any(name in config.get("design", "") for name in
                   ("winograd_network", "winograd_continuous", "combination_network", "combination_continuous")):
            continue
        if config.get("errors"):
            continue
        binary = archive / "offline_G2_w10_i16.bin"
        transformed.astype("<i2").tofile(binary)
        records = [{"source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
                    "tensor_sha256":hashlib.sha256(binary.read_bytes()).hexdigest(),
                    "layout":"Cout64,subkernel9,transform_row4,transform_col4;little-endian signed16 container",
                    "quantization":"nearest-even saturating signed10,fraction9",
                    "transformed_min":int(transformed.min()),"transformed_max":int(transformed.max()),
                    "logical_bits":14,"values":transformed.size,"bytes":binary.stat().st_size,
                    "inverse_scale":4,
                    "runtime_contract":"This offline tensor is equivalent evidence only; arbitrary incoming float weights still transform in the design load stage."}]
        with (archive / "offline_weights.csv").open("w",newline="") as out:
            writer = csv.DictWriter(out,fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
        print(archive.name,records[0]["transformed_min"],records[0]["transformed_max"])
    check_protected()


if __name__ == "__main__":
    main()
