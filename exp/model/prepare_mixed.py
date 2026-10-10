#!/usr/bin/env python3
"""Prepare real-ap_fixed references for the accepted Conv2 weight-only INT8 point."""
import json
import shutil
import numpy as np
from mixed_precision import mixed_model
from precision_scan import ROOT, load
from run_exp import write_json

weights = [load(ROOT/f"src/weights/conv{i+1}_weights_3x_flp.bin", "<f4", shape)
           for i, shape in enumerate(((64, 1, 9, 9), (32, 64, 1, 1), (1, 32, 5, 5)))]
biases = [load(ROOT/f"src/weights/conv{i+1}_biases_3x_flp.bin", "<f4", (n,)) for i, n in enumerate((64, 32, 1))]
folder = ROOT/"exp/numeric_reference/mixed_conv2w8/numpy_reference"
if folder.exists():
    raise RuntimeError("Reference already exists")
folder.mkdir(parents=True)
for path in sorted((ROOT/"test/set14").glob("*_LR_u8.bin")) + [ROOT/"test/set5/butterfly_3x_LR_u8.bin"]:
    image = load(path, np.uint8, (255, 255)).astype(np.float32)/np.float32(255)
    out, saturated = mixed_model(image, weights, biases, [10, 8, 10], [10]*4)
    if saturated:
        raise RuntimeError("Unexpected saturation")
    out.astype("<f4").tofile(folder/(path.name.split("_")[0]+"_output.bin"))

dest = ROOT/"designs/fixed_ref_mixed_raw"
if dest.exists():
    raise RuntimeError("Design already exists")
shutil.copytree(ROOT/"designs/fixed_ref_raw", dest)
path = dest/"srcnn.cpp"
text = path.read_text().replace("using A1 =", "using Weight2 = ap_fixed<8, 1, AP_RND_CONV, AP_SAT>;\nusing Acc2 = ap_fixed<AB + 11, 6, AP_RND_CONV, AP_SAT>;\nusing A1 =")
text = text.replace("b2[oc] = raw(Weight(biases2[oc]))", "b2[oc] = raw(Weight2(biases2[oc]))")
text = text.replace("raw(Weight(weights2[oc][ic][0][0]))", "raw(Weight2(weights2[oc][ic][0][0]))")
text = text.replace("a2[oc][y][x] = cast_raw<Acc1, A2>", "a2[oc][y][x] = cast_raw<Acc2, A2>")
path.write_text(text)

base = json.loads((ROOT/"exp/configs/E017.json").read_text())
base.update(id="E065", name="apfixed_mixed_conv2w8", design="designs/fixed_ref_mixed_raw", stage=1,
    precision="w10_8_10a10acc23_21_23", quick=True, csim_only=True, set14=True,
    defines={"EXP_W_BITS": 10, "EXP_A_BITS": 10}, numpy_reference=str(folder.relative_to(ROOT)),
    purpose="Confirm E062 Conv2-only eight-bit weights/biases on every supplied image using real ap_fixed input, parameter and layer-boundary casts with exact integer convolution.",
    changes="Independent fixed_ref_raw copy; Conv2 uses ap_fixed<8,1> and its exact 21-bit accumulator. Conv1/Conv3 remain ten-bit; all activations remain ten-bit.",
    interpretation="Bit comparison to independently predicted numpy output is mandatory for all 13 images. Full product fractions make integer-carrier sums identical to no-overflow ap_fixed arithmetic.",
    conclusion="Save mixed-precision provenance for phase-two Conv2 weight-only packing; complete Set14 still lacks comic.")
base.pop("quality_reference", None)
base.pop("reference", None)
write_json(ROOT/"exp/configs/E065.json", base)

dest = ROOT/"designs/fixed_ref_mixed"
if dest.exists():
    raise RuntimeError("Design already exists")
shutil.copytree(ROOT/"designs/fixed_ref", dest)
types = (dest/"types.h").read_text()
types = types.replace("using act1", "using weight2 = ap_fixed<8, 1, AP_RND_CONV, AP_SAT>;\nusing acc2mixed = ap_fixed<EXP_A_BITS + 11, 6, AP_RND_CONV, AP_SAT>;\nusing act1")
(dest/"types.h").write_text(types)
text = (dest/"srcnn.cpp").read_text()
text = text.replace("weight w1[N1][N0][F1][F1], w2[N2][N1][F2][F2], w3[N3][N2][F3][F3];",
                    "weight w1[N1][N0][F1][F1], w3[N3][N2][F3][F3];\n    weight2 w2[N2][N1][F2][F2];")
text = text.replace("bias b1[N1], b2[N2], b3[N3];", "bias b1[N1], b3[N3];\n    weight2 b2[N2];")
text = text.replace("acc2 sum =", "acc2mixed sum =")
(dest/"srcnn.cpp").write_text(text)
base.update(id="E066", name="full_apfixed_mixed_butterfly", design="designs/fixed_ref_mixed", set14=False,
    quality_reference="experiments/E065_apfixed_mixed_conv2w8/metrics.json",
    reference="exp/numeric_reference/mixed_conv2w8/numpy_reference/butterfly_output.bin",
    purpose="Verify the complete all-ap_fixed mixed network on butterfly, independently of native convolution carriers; use E065's separately measured 13-image PSNR only after exact matching.",
    changes="Independent all-ap_fixed fixed_ref copy with only Conv2 weight/bias and accumulator widths changed to 8/21. Boundary quantization unchanged.")
write_json(ROOT/"exp/configs/E066.json", base)
