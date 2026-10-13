#!/usr/bin/env python3
"""Float range profile and AP_RND_CONV/AP_SAT fake quantization scan."""
import argparse
import csv
import ctypes
import json
import math
from pathlib import Path
import subprocess
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "exp"))
from run_exp import FIELDS, append_log, check_protected, markdown_table, utc, write_json

H = W = 255
BORDER = np.ones((H, W), bool)
BORDER[6:-6, 6:-6] = False


def load(path, dtype, shape):
    array = np.fromfile(path, dtype=dtype)
    if array.size != math.prod(shape):
        raise ValueError("Wrong file size: " + str(path))
    return array.reshape(shape)


def integer_bits(maximum):
    return max(1, math.floor(math.log2(maximum)) + 2) if maximum > 0 else 1


def quantize(array, bits, integer):
    scaled = np.rint(np.ldexp(np.asarray(array, dtype=np.float64), bits - integer))
    lo, hi = -(2 ** (bits - 1)), 2 ** (bits - 1) - 1
    saturations = int(np.count_nonzero((scaled < lo) | (scaled > hi)))
    return np.clip(scaled, lo, hi), saturations


def boundary(raw, fraction, bits, integer):
    return quantize(np.ldexp(raw, -fraction), bits, integer)


def patches(a, kernel):
    a = np.pad(a, ((0, 0), (kernel // 2, kernel // 2), (kernel // 2, kernel // 2)), mode="edge")
    windows = np.lib.stride_tricks.sliding_window_view(a, (kernel, kernel), axis=(1, 2))
    return windows


def convolution(a, weights, bias, kernel, chunk=1020):
    window = patches(a, kernel)
    cout, cin = weights.shape[:2]
    result = np.empty((cout, H, W), dtype=np.result_type(a, weights))
    flattened = weights.reshape(cout, -1).T
    # Row blocks retain channel/tap order and avoid full-frame im2col allocation.
    rows = max(1, chunk // W)
    for y in range(0, H, rows):
        part = window[:, y:y + rows].transpose(1, 2, 0, 3, 4).reshape(-1, cin * kernel * kernel)
        out = part @ flattened + bias
        result[:, y:y + rows] = out.reshape(-1, W, cout).transpose(2, 0, 1)
    return result


def float_model(image, weights, biases):
    x = image[None]
    for layer, kernel in enumerate((9, 1, 5)):
        x = convolution(x, weights[layer], biases[layer], kernel)
        if layer != 2:
            x = np.maximum(x, 0)
    return x[0]


def fixed_model(image, weights, biases, wi, bi, ai, wb, ab):
    x, saturations = quantize(image[None], ab, ai[0])
    acc_widths = []
    details = []
    for layer, kernel in enumerate((9, 1, 5)):
        w, sw = quantize(weights[layer], wb, wi[layer])
        b, sb = quantize(biases[layer], wb, bi[layer])
        af, wf, bf = ab - ai[layer], wb - wi[layer], wb - bi[layer]
        frac = max(af + wf, bf)
        exact_limit = (2 ** (ai[layer] - 1)) * np.max(np.sum(np.abs(np.ldexp(w, -wf)), axis=(1, 2, 3)))
        exact_limit += np.max(np.abs(np.ldexp(b, -bf)))
        acc_i = integer_bits(float(exact_limit))
        acc_width = acc_i + frac
        if acc_width > 52:
            raise ValueError("Exact float64 integer arithmetic limit exceeded")
        raw = convolution(x, w, np.ldexp(b, frac - bf), kernel)
        if frac != af + wf:
            # Scale only the product when bias has more fractional bits.
            raw = (raw - np.ldexp(b, frac - bf)[:, None, None]) * 2 ** (frac - af - wf)
            raw += np.ldexp(b, frac - bf)[:, None, None]
        if np.max(np.abs(raw)) >= 2 ** (acc_width - 1):
            raise ValueError("Accumulator overflow")
        if layer != 2:
            raw = np.maximum(raw, 0)
        x, sa = boundary(raw, frac, ab, ai[layer + 1])
        saturations += sw + sb + sa
        acc_widths.append(acc_width)
        details.append({"acc_w": acc_width, "acc_i": acc_i, "acc_f": frac,
                        "observed_raw_max": float(np.max(np.abs(raw))), "saturations": sw + sb + sa})
    return np.ldexp(x[0], -(ab - ai[-1])).astype(np.float32), saturations, acc_widths, details


def psnr(output, gt):
    error = np.mean((output.astype(np.float64) - gt.astype(np.float64)) ** 2)
    return -10 * math.log10(float(error))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", default="E010")
    args = parser.parse_args()
    check_protected()
    work = ROOT / "workspace/exp_runs" / args.id
    archive = ROOT / "experiments" / (args.id + "_precision_scan")
    if archive.exists():
        raise RuntimeError("Experiment ID exists")
    work.mkdir(parents=True, exist_ok=True)
    archive.mkdir(parents=True)
    shared = work / ("golden.dylib" if sys.platform == "darwin" else "golden.so")
    compile_command = ["clang++" if sys.platform == "darwin" else "g++", "-O3", "-std=c++14", "-ffp-contract=off",
                       "-shared", "-fPIC", str(ROOT / "exp/model/golden_bridge.cpp"), "-o", str(shared)]
    subprocess.run(compile_command, check=True)
    bridge = ctypes.CDLL(str(shared))
    ptr = np.ctypeslib.ndpointer(dtype=np.float32, flags="C_CONTIGUOUS")
    bridge.forward.argtypes = [ptr] * 8 + [np.ctypeslib.ndpointer(dtype=np.float64, flags="C_CONTIGUOUS")]
    bridge.original_forward.argtypes = [ptr] * 8
    bridge.forward.restype = bridge.original_forward.restype = None
    weights = [load(ROOT / f"src/weights/conv{i + 1}_weights_3x_flp.bin", "<f4", shape)
               for i, shape in enumerate(((64, 1, 9, 9), (32, 64, 1, 1), (1, 32, 5, 5)))]
    biases = [load(ROOT / f"src/weights/conv{i + 1}_biases_3x_flp.bin", "<f4", (n,))
              for i, n in enumerate((64, 32, 1))]
    inputs = sorted((ROOT / "test/set14").glob("*_LR_u8.bin"))
    if len(inputs) != 13:
        raise RuntimeError("Unexpected supplied dataset membership; review manifest")
    images, ranges, float_checks = [], [], []
    for path in inputs:
        name = path.name.split("_")[0]
        image = load(path, np.uint8, (H, W)).astype(np.float32) / np.float32(255)
        gt = load(path.with_name(path.name.replace("LR", "GT")), np.uint8, (H, W)).astype(np.float32) / np.float32(255)
        output, original = np.empty_like(image), np.empty_like(image)
        profile = np.zeros(6, np.float64)
        call = [image, weights[0], biases[0], weights[1], biases[1], weights[2], biases[2]]
        bridge.forward(*call, output, profile)
        bridge.original_forward(*call, original)
        if not np.array_equal(output.view(np.uint32), original.view(np.uint32)):
            raise ValueError("Range profiling differs from unchanged golden: " + name)
        predicted = float_model(image, weights, biases)
        model_mse = float(np.mean((predicted.astype(np.float64) - original) ** 2))
        if model_mse > 1e-12:
            raise ValueError("Unquantized numpy model disagrees: " + name)
        float_checks.append({"image": name, "numpy_mse": model_mse,
                             "numpy_border_mse": float(np.mean((predicted.astype(np.float64) - original)[BORDER] ** 2)),
                             "profile_bit_exact": True, "golden_psnr": psnr(original, gt)})
        images.append((name, image, gt, original))
        ranges.append(profile)
        print("PROFILE", name, profile.tolist(), "numpy_mse", model_mse, flush=True)
    max_ranges = np.max(ranges, axis=0)
    wi = [integer_bits(float(np.max(np.abs(w)))) for w in weights]
    bi = [integer_bits(float(np.max(np.abs(b)))) for b in biases]
    ai = [2] + [integer_bits(float(max_ranges[2 * i + 1])) for i in range(3)]
    range_rows = []
    for layer in range(3):
        for tensor, maximum, integer in (("weight", np.max(np.abs(weights[layer])), wi[layer]),
                                         ("bias", np.max(np.abs(biases[layer])), bi[layer]),
                                         ("activation", max_ranges[2 * layer + 1], ai[layer + 1]),
                                         ("partial_accumulator", max_ranges[2 * layer], integer_bits(max_ranges[2 * layer]))):
            range_rows.append({"layer": layer + 1, "tensor": tensor, "max_abs": float(maximum), "integer_bits": integer})
    config = {"id": args.id, "stage": 1, "rounding": "AP_RND_CONV (ties to even)", "overflow": "AP_SAT",
              "weight_integer_bits": wi, "bias_integer_bits": bi, "activation_integer_bits": ai,
              "weight_widths": [16, 12, 10, 8], "activation_widths": [16, 12, 10, 8],
              "image_count": len(images), "compile_command": compile_command,
              "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "numpy_version": np.__version__, "psnr": "normalized float, no clipping or cropping",
              "accumulator": "full product precision, exact bias alignment, analytical worst-case bound"}
    write_json(archive / "config.json", config)
    scan, detail = [], []
    for wb in (16, 12, 10, 8):
        for ab in (16, 12, 10, 8):
            qualities, drops, widths, per_layer = [], [], [], None
            saturation_count = 0
            for name, image, gt, original in images:
                out, saturated, widths, per_layer = fixed_model(image, weights, biases, wi, bi, ai, wb, ab)
                p, g = psnr(out, gt), psnr(original, gt)
                qualities.append(p)
                drops.append(p - g)
                saturation_count += saturated
                detail.append({"w_bits": wb, "a_bits": ab, "image": name, "psnr": p, "golden_psnr": g,
                               "delta_psnr": p - g, "border_mse": float(np.mean((out.astype(np.float64) - original)[BORDER] ** 2)),
                               "saturations": saturated})
            row = {"id": args.id, "w_bits": wb, "a_bits": ab, "psnr": float(np.mean(qualities)),
                   "delta_psnr": float(np.mean(drops)), "min_image_delta": min(drops),
                   "pass_available": float(np.mean(drops)) >= -.1 and saturation_count == 0,
                   "saturations": saturation_count, "image_count": len(images),
                   "acc_widths": "/".join(map(str, widths))}
            scan.append(row)
            write_json(archive / f"w{wb}a{ab}.json", {**config, "w_bits": wb, "a_bits": ab, "accumulators": per_layer})
            print("SCAN", row, flush=True)
    for filename, rows in (("data.csv", scan), ("per_image.csv", detail), ("ranges.csv", range_rows), ("float_validation.csv", float_checks)):
        with (archive / filename).open("w", newline="") as out:
            writer = csv.DictWriter(out, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    acceptable = sorted([s for s in scan if s["pass_available"]], key=lambda s: (s["w_bits"] * s["a_bits"], s["w_bits"] + s["a_bits"]))
    representatives = [(16, 16), (8, 8)]
    if acceptable:
        best = acceptable[0]
        representatives.append((best["w_bits"], best["a_bits"]))
    representatives = list(dict.fromkeys(representatives))
    write_json(archive / "representatives.json", representatives)
    text = f"# {args.id}: precision scan\n\n## 1. Purpose and hypothesis / 目的与假设\n\nFind low-precision settings retaining mean PSNR within 0.1 dB of float golden, and determine integer ranges using all supplied images. Exact integer sums permit reorder-invariant architecture checks. No HLS performance prediction is made by this software-only experiment.\n\n"
    text += f"## 2. Changes / 改动\n\nNew profiling bridge and numpy fake-quant model. Source commit `{config['source_commit']}`; protected original sources are included unchanged in an independent comparison.\n\n"
    text += "## 3. Configuration / 配置\n\n" + markdown_table(range_rows, ["layer", "tensor", "max_abs", "integer_bits"])
    text += "\nAP_RND_CONV ties-to-even, AP_SAT signed saturation. Weights and bias each use scanned W bits with independently measured integer bits; layer outputs and input use A bits. Accumulator keeps exact product and bias fractions and has an analytical bound covering all representable input activations. Float64 BLAS acts on integers with every intermediate below 2^52.\n\n"
    text += f"## 4. Reproduction / 复现\n\n```sh\nworkspace/exp_runs/_tools/venv/bin/python exp/model/precision_scan.py --id {args.id}\n```\n\n"
    text += "## 5. Results / 结果\n\n" + markdown_table(scan, list(scan[0]))
    text += "\nFloat validation: see float_validation.csv. No pipelined-loop II or module resource report; this is CPU numerical analysis.\n\n"
    text += "## 6. Interpretation / 解读\n\nPending real ap_fixed representative verification. All 13 supplied pairs evaluated; missing comic prevents full Set14 acceptance. Bias and layer-output casts are explicit; partial-sum bounds include intermediate accumulation, not just final outputs.\n\n"
    text += "## 7. Conclusion and next step / 结论与下一步\n\nRepresentatives: " + str(representatives) + ". Verify using actual AMD ap_fixed before treating fake-quant quality as established.\n\n"
    text += f"## 8. Raw files / 原始文件位置\n\n`workspace/exp_runs/{args.id}/`; CSV/config archive in this directory.\n"
    (archive / (args.id + ".md")).write_text(text, encoding="utf-8")
    row = dict.fromkeys(FIELDS, "")
    row.update(id=args.id, time=utc(), stage=1, design="numpy_precision_scan", precision_w_a_acc="16/12/10/8 scan",
               status="analysis_complete", git_commit=config["source_commit"], md_path=f"{args.id}_precision_scan/{args.id}.md",
               notes="13 supplied pairs; full Set14 acceptance pending; real ap_fixed validation pending")
    results = ROOT / "experiments/results.csv"
    header = not results.exists()
    with results.open("a", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=FIELDS)
        if header:
            writer.writeheader()
        writer.writerow(row)
    append_log(args.id + ": completed range analysis and 16-point scan on all 13 supplied pairs")
    check_protected()


if __name__ == "__main__":
    main()
