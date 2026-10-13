#!/usr/bin/env python3
"""Freeze full signed-INT16 pair hypotheses before implementing the kernels."""
import subprocess
import sys
from plan_arch import plan
from run_exp import ROOT, append_log, lock


def main():
    base = {
        "stage": "arch_pe", "series": "P", "scope": "PE", "clock": 4, "T": 1,
        "settings": "/home/lipuze/amdfpga/2026.1/Vitis/settings64.sh",
        "design": "designs/packing_int16_pe", "top": "packing16_pe",
        "precision": "signed16_signed16_exact32_pair",
        "tb_files": ["exp/tb/packing16_validate.cpp"],
        "ii_targets": {"pack16_terms": 1},
        "notes": "PE only; two complete signed16 products per term, no network latency or Set14 claim",
        "changes": "New independent INT16 PE and testbench. Existing INT8/exact10 designs remain frozen. All modes use the same64-term array interface and exact int64 oracle.",
        "conclusion": "Compare complete32-bit product equality, DSP, LUT, FF, achieved II and clock. A one-DSP mixed implementation still spends LUT multipliers; integrate only after a demonstrated network budget.",
    }
    cases = [
        ("P13", "int16_direct_pair", 0, 2, 100, 120, 72,
         "Control: compute a*c and b*c as two signed16x16 DSP products. Expect two DSP48E2 cells and II1; use this matched pair control rather than doubling unrelated E051 array/control resources."),
        ("P14", "int16_limb_packing", 1, 4, 500, 500, 80,
         "Split every signed16 value as unsigned low8 plus256*signed high8. Four packed byte-product pairs reconstruct both complete32-bit products exactly. Each low byte product fits a signed18 field, including unsigned255*255=65025. Expect four DSP48E2 multipliers per pair: exact generic16-bit limb packing alone loses DSP area versus two direct products."),
        ("P15", "int16_overlap_fabric_repair", 2, 1, 900, 500, 80,
         "Test exact overlapping-field recovery: let b=L+256*R with signed8 L and signed9 R, pack q=(a<<10)+L in signed27, and compute q*c in one27x16 DSP. A fabric8x16 product L*c removes the overlapping low field; (q*c-L*c)>>10 gives the complete a*c. A fabric9x16 product R*c reconstructs complete b*c. Expect one DSP plus two fabric multipliers, a43-bit subtract and a33-bit recombination. This is not two unrestricted16x16 products performed solely by one DSP."),
        ("P16", "int16_direct_mixed_control", 3, 1, 650, 400, 76,
         "Matched mixed-resource control: a*c uses one DSP and b*c is one direct signed16x16 fabric multiplier. Compare against P15 at the same pair rate to establish whether overlapping packing improves LUT, pipeline or clock beyond ordinary DSP/fabric mixing."),
    ]
    for exp_id, name, mode, dsp, lut, ff, cycles, purpose in cases:
        config = {**base, "id": exp_id, "name": name,
                  "defines": {"EXP_PACK16_MODE": mode}, "purpose": purpose,
                  "interpretation": "A complete signed16x16 product needs32 bits. Nonoverlapping two-product fields need at least gap32, making the coefficient port48 bits, beyond DSP48E2's27-bit input; splitting a coefficient alone leaves8x16 products needing24 bits and a32-bit packed port. P14 therefore splits both operands. P15 explicitly pays fabric recovery for overlapping fields. Count every DSP/fabric operation, compare P13/P16 controls, and retain failures or missed II without changing numerical gates.",
                  "estimates": {"DSP": dsp, "BRAM18K": 0, "URAM": 0, "LUT": lut,
                                "FF": ff, "T": 1, "latency_cycles": cycles,
                                "basis": "64 independent pairs plus8-16 pipeline cycles; no internal frame memories. Direct16x16 uses one DSP per product. Byte-limb pairs use four27x9/8 DSP products. Overlap repair uses one27x16 DSP plus fabric8x16 and9x16 products; the mixed control uses one DSP plus fabric16x16. LUT/FF values reserve operand repair, carry chains, pipelining and array control; they are hypotheses, not primitive measurements."}}
        plan(config)
        subprocess.run([sys.executable, str(ROOT / "exp/commit_exp.py"), exp_id,
                        "plan_"+name], cwd=ROOT, check=True)
    with lock(ROOT / "workspace/exp_runs/.results.lock", wait_timeout=120):
        append_log("P13-P16: user requested complete INT16 packing research; preplanned direct, four-DSP byte limbs, one-DSP overlap/fabric repair and ordinary mixed controls. Exact32-bit product checks cover all16-bit values in each operand role, boundary cubes and deterministic random triples. Existing final verification queues continue.")
    subprocess.run([sys.executable, str(ROOT / "exp/update_arch_progress.py")], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "exp/commit_exp.py"), "P13",
                    "freeze_int16_research_queue"], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
