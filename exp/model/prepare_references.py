#!/usr/bin/env python3
"""Generate independently predicted outputs and actual ap_fixed configurations."""
import json
from pathlib import Path
import sys
import numpy as np
from precision_scan import ROOT, load, fixed_model


def main():
    base = json.loads((ROOT / "experiments/E010_precision_scan/config.json").read_text())
    weights = [load(ROOT / f"src/weights/conv{i + 1}_weights_3x_flp.bin", "<f4", shape)
               for i, shape in enumerate(((64, 1, 9, 9), (32, 64, 1, 1), (1, 32, 5, 5)))]
    biases = [load(ROOT / f"src/weights/conv{i + 1}_biases_3x_flp.bin", "<f4", (n,))
              for i, n in enumerate((64, 32, 1))]
    for exp_id, wb, ab in (("E014", 16, 16), ("E012", 10, 10), ("E013", 8, 8)):
        folder = ROOT / "exp/numeric_reference" / f"w{wb}a{ab}" / "numpy_reference"
        folder.mkdir(parents=True, exist_ok=True)
        for path in sorted((ROOT / "test/set14").glob("*_LR_u8.bin")) + [ROOT / "test/set5/butterfly_3x_LR_u8.bin"]:
            name = path.name.split("_")[0]
            image = load(path, np.uint8, (255, 255)).astype(np.float32) / np.float32(255)
            out, _, _, _ = fixed_model(image, weights, biases, base["weight_integer_bits"],
                                       base["bias_integer_bits"], base["activation_integer_bits"], wb, ab)
            out.astype("<f4").tofile(folder / (name + "_output.bin"))
        config = {"id": exp_id, "name": f"apfixed_w{wb}a{ab}", "stage": 1, "design": "designs/fixed_ref",
                  "clock": 10, "fixed": True, "set14": True, "csim_only": True,
                  "precision": f"w{wb}a{ab}acc{wb + ab + 3}", "defines": {"EXP_W_BITS": wb, "EXP_A_BITS": ab},
                  "numpy_reference": str(folder.relative_to(ROOT)),
                  "settings": "/home/lipuze/amdfpga/2026.1/Vitis/settings64.sh", "csim_timeout": 2700,
                  "purpose": "Verify fake-quant predictions with actual AMD ap_fixed on butterfly and every supplied Set14 pair.",
                  "changes": "Independent fixed reference retains golden external float signature; internal weights/biases and activations use AP_RND_CONV/AP_SAT. Exact product-fraction accumulators.",
                  "interpretation": "Pending real ap_fixed output and bit comparison with numpy.",
                  "conclusion": "Save actual ap_fixed butterfly output for subsequent architecture bit-exact checks."}
        (ROOT / f"exp/configs/{exp_id}.json").write_text(json.dumps(config, indent=2) + "\n")
        print(exp_id, folder, flush=True)
    cfg = json.loads((ROOT / "exp/configs/E014.json").read_text())
    cfg.update(id="E027", name="auto_fixed16", stage=2, csim_only=False, set14=False,
               purpose="Isolate type-change benefit without streaming architectural changes; retain full intermediate feature maps.")
    (ROOT / "exp/configs/E027.json").write_text(json.dumps(cfg, indent=2) + "\n")


if __name__ == "__main__":
    main()
