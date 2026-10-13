#!/usr/bin/env python3
"""Preplan two legal Conv3 window channels after the measured4096-bit limit."""
import json
import subprocess
import sys
from plan_arch import plan
from run_exp import ROOT

CASES = (("F08","F03","continuous_direct_r2"),("F09","F04","continuous_direct_r2"),
         ("F10","F05","continuous_direct_r2"),("F11","F06","continuous_direct_r2"),
         ("F12","F07","continuous_direct_r2"),("W14","W11","winograd_continuous_r2"),
         ("W15","W12","winograd_continuous_r2"),("W16","W13","winograd_continuous_r2"),
         ("C10","C08","winograd_mixed_packing_r2"),("C11","C09","winograd_mixed_packing_r2"))


def main():
    for exp_id,parent,design in CASES:
        base = json.loads((ROOT / "exp/configs" / (parent+".json")).read_text())
        config = {**base,"id":exp_id,"name":base["name"]+"_split4000","design":"designs/"+design,
                  "purpose":"W11 C simulation passes exactly but synthesis rejects the8000-bit aggregated Conv3 stream with HLS214-256: maximum4096 bits. Preserve the continuous schedule and represent one800-element window as two25x16-channel4000-bit packets, each below the measured limit. Both streams produce/consume65025 packets per frame; no quantization or MAC change. "+base["purpose"],
                  "changes":"New independent source based on "+parent+". Replace the single oversized window stream with two synchronized channel halves. Each uses a two-entry LUTRAM FIFO; compute retains the complete window and chooses the correct half for each input channel. All first-phase and attempted sources stay frozen.",
                  "estimates":{**base["estimates"],"LUT":base["estimates"].get("LUT",55000)+100,
                               "basis":base["estimates"]["basis"]+" Two4000-bit channels keep the same8000 stored payload bits per window and two-entry depths; reserve100 additional control LUT for the second FIFO. Arithmetic DSP,T and cycle estimates stay identical. Aggregation legality is required before any resource/speed claim."},
                  "interpretation":"Compare the frozen estimates with parsed hardware reports. This is a representation fix for the compiler's4096-bit aggregate limit, not a precision relaxation. Check both stream counts and achievedII; final selected points still require full-supplied-image verification and finite-FIFO RTL cosimulation."}
        plan(config)
        subprocess.run([sys.executable,str(ROOT / "exp/commit_exp.py"),exp_id,"plan_split4000_"+parent],cwd=ROOT,check=True)


if __name__ == "__main__":
    main()
