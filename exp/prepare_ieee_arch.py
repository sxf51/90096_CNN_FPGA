#!/usr/bin/env python3
"""Plan exact integer-carrier to IEEE-float conversion probes."""
import subprocess
import sys
from plan_arch import plan
from run_exp import ROOT


def main():
    for exp_id,legacy,dsp,lut,ff in (("F16",0,0,250,180),("F17",1,3,550,550)):
        config = {"id":exp_id,"name":"ieee_decode_"+("legacy_control" if legacy else "bit_exact"),
                  "series":"F","stage":"arch_pe","scope":"PE","design":"designs/ieee_decode_pe",
                  "top":"ieee_decode_pe","tb_files":["exp/tb/ieee_decode.cpp"],"clock":3.33,"T":1,
                  "precision":"raw10_frac8_float32_exact","defines":{"EXP_LEGACY_DECODE":legacy},
                  "settings":"/home/lipuze/amdfpga/2026.1/Vitis/settings64.sh",
                  "ii_targets":{"decode_words":1},
                  "purpose":"F08 write_output reports3DSP,534LUT,547FF and3.239ns estimated clock for float(raw10)/256. Every raw10 value is exactly representable in binary32. Exhaust all1024 raw values across three orderings, including zero,-512,511 and negative fractions, comparing binary float bits to ordinary division. "+
                            ("Use ordinary conversion/division as the isolated control." if legacy else "Construct sign/exponent/significand using the installed hls::fp_struct<float>; no floating arithmetic, unsafe pointer aliasing, rounding or precision change."),
                  "changes":"Independent PE and new exp/tb checker; no SRCNN source/interface/data changed.",
                  "estimates":{"DSP":dsp,"BRAM18K":0,"URAM":0,"LUT":lut,"FF":ff,"T":1,
                               "latency_cycles":1045,"basis":"1024 independent words withII1 and<=21 pipeline cycles. Legacy resource allowance uses the measured F08 write module; direct IEEE construction uses a10-bit sign/magnitude, highest-set-bit selector and bounded significand shift. These are PE counts only and cannot rank as frame latency."},
                  "interpretation":"Compare exact float bits,II1,DSP and converter clock. A zero-DSP claim requires the actual report. Only integrate a passing exact microkernel into a new full-network design.",
                  "conclusion":"Use measured conversion evidence to decide whether a faster-clock full-network follow-up is justified.",
                  "notes":"PE only; conversion-probe cycles are excluded from network rankings"}
        plan(config)
        subprocess.run([sys.executable,str(ROOT / "exp/commit_exp.py"),exp_id,"plan_exact_ieee_conversion"],cwd=ROOT,check=True)


if __name__ == "__main__":
    main()
