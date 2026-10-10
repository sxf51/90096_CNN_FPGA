#!/usr/bin/env python3
"""Layer-specific INT8 eligibility study on every supplied image."""
import csv
import ctypes
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
from precision_scan import (ROOT, H, W, BORDER, load, quantize, convolution,
                            boundary, integer_bits, psnr)
from run_exp import (FIELDS, append_log, check_protected, lock, markdown_table,
                     utc, write_json)


def mixed_model(image, weights, biases, widths_w, widths_a):
    ai = (2, 2, 3, 2)
    x, count = quantize(image[None], widths_a[0], ai[0])
    for layer, kernel in enumerate((9, 1, 5)):
        wb, ab = widths_w[layer], widths_a[layer]
        w, sw = quantize(weights[layer], wb, 1)
        b, sb = quantize(biases[layer], wb, 1)
        frac = ab - ai[layer] + wb - 1
        raw = convolution(x, w, np.ldexp(b, ab - ai[layer]), kernel)
        limit = 2 ** (ai[layer] - 1) * np.max(np.sum(np.abs(np.ldexp(w, -(wb - 1))), axis=(1, 2, 3)))
        limit += np.max(np.abs(np.ldexp(b, -(wb - 1))))
        bits = integer_bits(float(limit)) + frac
        if bits > 52 or np.max(np.abs(raw)) >= 2 ** (bits - 1):
            raise ValueError("Accumulator precision/overflow violation")
        if layer != 2:
            raw = np.maximum(raw, 0)
        x, sa = boundary(raw, frac, widths_a[layer + 1], ai[layer + 1])
        count += sw + sb + sa
    return np.ldexp(x[0], -(widths_a[3] - 2)).astype(np.float32), count


def main():
    check_protected()
    exp_id = "E062"
    archive = ROOT / "experiments/E062_layer_int8_scan"
    work = ROOT / "workspace/exp_runs/E062"
    if archive.exists() or work.exists():
        raise RuntimeError("Existing ID")
    archive.mkdir()
    work.mkdir()
    shared = work / ("golden.dylib" if sys.platform == "darwin" else "golden.so")
    command = ["clang++" if sys.platform == "darwin" else "g++", "-O3", "-std=c++14", "-ffp-contract=off",
               "-shared", "-fPIC", str(ROOT / "exp/model/golden_bridge.cpp"), "-o", str(shared)]
    subprocess.run(command, check=True)
    bridge = ctypes.CDLL(str(shared))
    bridge.original_forward.argtypes = [np.ctypeslib.ndpointer(dtype=np.float32, flags="C_CONTIGUOUS")] * 8
    bridge.original_forward.restype = None
    weights = [load(ROOT / f"src/weights/conv{i+1}_weights_3x_flp.bin", "<f4", shape)
               for i, shape in enumerate(((64, 1, 9, 9), (32, 64, 1, 1), (1, 32, 5, 5)))]
    biases = [load(ROOT / f"src/weights/conv{i+1}_biases_3x_flp.bin", "<f4", (n,))
              for i, n in enumerate((64, 32, 1))]
    images = []
    for path in sorted((ROOT / "test/set14").glob("*_LR_u8.bin")):
        image = load(path, np.uint8, (H, W)).astype(np.float32) / np.float32(255)
        gt = load(path.with_name(path.name.replace("LR", "GT")), np.uint8, (H, W)).astype(np.float32) / np.float32(255)
        golden = np.empty_like(image)
        bridge.original_forward(image, weights[0], biases[0], weights[1], biases[1], weights[2], biases[2], golden)
        images.append((path.name.split("_")[0], image, gt, golden))
    if len(images) != 13:
        raise RuntimeError("Unexpected dataset membership")
    cases = [("uniform10", [10]*3, [10]*4), ("uniform16", [16]*3, [16]*4)]
    for base in (10, 16):
        for layer in range(3):
            wb = [base]*3
            wb[layer] = 8
            cases.append((f"w8_layer{layer+1}_base{base}", wb, [base]*4))
    for activation in range(3):
        ab = [10]*4
        ab[activation] = 8
        cases.append((f"a8_boundary{activation}_base10", [10]*3, ab))
    for layer in range(3):
        wb, ab = [10]*3, [10]*4
        wb[layer], ab[layer] = 8, 8
        cases.append((f"packed_layer{layer+1}_base10", wb, ab))
    cases.append(("packed_layer23_base10", [10, 8, 8], [10, 8, 8, 10]))
    config = {"id": exp_id, "stage": 1, "image_count": 13, "cases": cases,
              "rounding": "AP_RND_CONV", "overflow": "AP_SAT", "full_product_fractions": True,
              "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
              "psnr": "normalized float without clipping/cropping", "compile_command": command}
    write_json(archive / "config.json", config)
    details, scan = [], []
    for name, wb, ab in cases:
        point = []
        for image_name, image, gt, golden in images:
            out, saturated = mixed_model(image, weights, biases, wb, ab)
            p, g = psnr(out, gt), psnr(golden, gt)
            detail = {"id": exp_id, "point": name, "image": image_name, "weights": "/".join(map(str, wb)),
                      "activations": "/".join(map(str, ab)), "psnr": p, "delta_psnr": p-g,
                      "border_mse": float(np.mean((out.astype(np.float64)-golden)[BORDER]**2)), "saturations": saturated}
            details.append(detail)
            point.append(detail)
        row = {"id": exp_id, "point": name, "weights": "/".join(map(str, wb)), "activations": "/".join(map(str, ab)),
               "psnr": float(np.mean([p["psnr"] for p in point])),
               "delta_psnr": float(np.mean([p["delta_psnr"] for p in point])),
               "saturations": sum(p["saturations"] for p in point), "image_count": 13}
        row["pass_available"] = row["delta_psnr"] >= -.1 and not row["saturations"]
        scan.append(row)
        print(json.dumps(row), flush=True)
    for name, rows in (("data.csv", scan), ("per_image.csv", details)):
        with (archive/name).open("w", newline="") as out:
            writer = csv.DictWriter(out, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    text = f"# {exp_id}: layer-specific INT8 precision\n\n"
    text += "## 1. Purpose and hypothesis / 目的与假设\n\nCheck whether a single INT8 layer can retain the 0.1 dB quality gate even though uniform INT8 fails. Software-only study; no DSP or latency claim.\n\n"
    text += f"## 2. Changes / 改动\n\nGeneralized layer widths with the unchanged E010 integer-fraction semantics; independently compiled unchanged golden. Source commit `{config['source_commit']}`.\n\n"
    text += "## 3. Configuration / 配置\n\n" + markdown_table([{"parameter": k, "value": v} for k, v in config.items()], ["parameter", "value"])
    text += "\n## 4. Reproduction / 复现\n\n```sh\nworkspace/exp_runs/_tools/venv/bin/python exp/model/mixed_precision.py\n```\n\nUse a new ID on rerun.\n\n"
    text += "## 5. Results / 结果\n\n" + markdown_table(scan, list(scan[0]))
    text += "\nNo HLS loop/module data: numerical study only. Per-image border MSE in per_image.csv.\n\n"
    text += "## 6. Interpretation / 解读\n\nEach point includes every supplied image and retains full fractions without accumulator overflow. An accepted fake-quant point still needs actual ap_fixed confirmation before hardware integration. Missing comic prevents full Set14 acceptance.\n\n"
    text += "## 7. Conclusion and next step / 结论与下一步\n\nUse measured layer eligibility to constrain phase-two packing. If no genuine INT8 layer passes, exact integer decomposition can preserve w10 precision.\n\n"
    text += "## 8. Raw files / 原始文件位置\n\n`workspace/exp_runs/E062/`; all numerical evidence archived here.\n"
    (archive/"E062.md").write_text(text)
    row = dict.fromkeys(FIELDS, "")
    row.update(id=exp_id, time=utc(), stage=1, design="numpy_layer_precision_scan", precision_w_a_acc="mixed layer scan",
               status="analysis_complete", git_commit=config["source_commit"], md_path=archive.name+"/E062.md",
               notes="13 supplied images; actual mixed-ap_fixed confirmation pending")
    with lock(ROOT/"workspace/exp_runs/.results.lock", wait_timeout=120):
        with (ROOT/"experiments/results.csv").open("a", newline="") as out:
            csv.DictWriter(out, fieldnames=FIELDS).writerow(row)
        append_log("E062: completed layer-specific INT8 eligibility study on 13 supplied pairs")
    check_protected()
    subprocess.run([sys.executable, str(ROOT/"exp/commit_exp.py"), exp_id, "layer_int8_scan"], check=True)


if __name__ == "__main__":
    main()
