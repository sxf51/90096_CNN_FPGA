#!/usr/bin/env python3
"""Generate a separately owned exact integer streaming control."""
import json
import shutil
from run_exp import ROOT, write_json


def replace(text, old, new):
    if old not in text:
        raise RuntimeError("Missing template: " + old)
    return text.replace(old, new)


destination = ROOT / "designs/dataflow_int"
if destination.exists():
    raise RuntimeError("Design already exists")
shutil.copytree(ROOT / "designs/dataflow_dsp", destination)
types = (destination / "types.h").read_text()
start = types.index("#if EXP_FIXED\nusing weight")
end = types.index("struct pixel1", start)
types = types[:start] + '#include "integer_numeric.inc"\n' + types[end:]
shutil.copyfile(ROOT / "exp/architectures/integer_numeric.inc", destination / "integer_numeric.inc")
types = types.replace("#include <ap_fixed.h>", "#include <ap_fixed.h>\n#include <cstdint>\n#include <type_traits>")
(destination / "types.h").write_text(types)
for filename in ("srcnn.cpp", "conv1.cpp"):
    path = destination / filename
    text = path.read_text()
    text = replace(text, "input(in[0][i / W][i % W])", "encode_input(in[0][i / W][i % W])") if filename == "srcnn.cpp" else replace(text, "input(in[0][y][x])", "encode_input(in[0][y][x])")
    if filename == "srcnn.cpp":
        for parameter, raw in (("biases[oc]", "bias1(biases[oc])"), ("biases[0]", "bias3(biases[0])")):
            text = replace(text, " = " + parameter + ";", " = " + raw + ";")
        # Conv2 shares the Conv1 bias scale; Conv3 uses one fewer fractional bit.
        text = replace(text, "sum > 0 ? act1(sum) : act1(0)", "relu1(sum)")
        text = replace(text, "sums[oc] > 0 ? act1(sums[oc]) : act1(0)", "relu1(sums[oc])")
        text = replace(text, "sum > 0 ? act2(sum) : act2(0)", "relu2(sum)")
        text = replace(text, "sums[oc] > 0 ? act2(sums[oc]) : act2(0)", "relu2(sums[oc])")
        text = replace(text, "out.write(output(sum))", "out.write(quantize<EXP_W_BITS - 2>(sum))")
        text = replace(text, "static_cast<float>(stream.read())", "decode(stream.read())")
        loads = {
            "weights1[i / 81][0][(i % 81) / 9][i % 9]": "encode_weight(weights1[i / 81][0][(i % 81) / 9][i % 9])",
            "weights2[i / N1][i % N1][0][0]": "encode_weight(weights2[i / N1][i % N1][0][0])",
            "weights3[0][i / 25][(i % 25) / 5][i % 5]": "encode_weight(weights3[0][i / 25][(i % 25) / 5][i % 5])",
            "biases1[i]": "encode_weight(biases1[i])", "biases2[i]": "encode_weight(biases2[i])",
            "biases3[0]": "encode_weight(biases3[0])"}
        for old, new in loads.items():
            text = replace(text, " = " + old + ";", " = " + new + ";")
    else:
        text = replace(text, "bias(biases[oc])", "encode_weight(biases[oc])")
        text = replace(text, "weight(weights[oc][0][tap / 9][tap % 9])", "encode_weight(weights[oc][0][tap / 9][tap % 9])")
        text = replace(text, "acc1 sum = qb[oc]", "acc1 sum = bias1(qb[oc])")
        text = replace(text, "static_cast<float>(sum > 0 ? act1(sum) : act1(0))", "decode(relu1(sum))")
    path.write_text(text)
config = json.loads((ROOT / "exp/configs/E047.json").read_text())
config.update(id="E048", name="dataflow_integer_T32", design="designs/dataflow_int",
    purpose="Measure explicit integer carriers with unchanged full-product fractions. Paper MAC budget "
            "162/64/25 = 251 DSP; buffer footprint as E047 (168 BRAM18K); compute floor 2080800 cycles. "
            "Simpler nearest-even boundary logic should reduce LUT and simulation time.",
    changes="Independent E047 copy. Actual ap_fixed input/parameter casts; explicit raw-integer full "
            "products, bias scale, nearest-even layer rounding and saturation. CPU uses matching native "
            "signed carriers under the proven no-overflow bounds; synthesis uses ap_int.",
    interpretation="Compare bit identity, inferred resource mapping and timing with E047. CPU arithmetic "
                   "and synthesized arithmetic share the exact same convolution, padding and cast code.",
    conclusion="Use only after strict E019/E017 butterfly comparison; retain provisional 13-image precision.")
write_json(ROOT / "exp/configs/E048.json", config)
