"""Strict WS-F evidence gates, independent of the old two-frame reload gate."""
import json
import re
from run_exp import number


def check_c_sequence(result, cold=False):
    flags = [0] if cold else [1, 0, 1, 0]
    if (result.get("csim_pass") is not True or result.get("bit_exact") is not True or
            result.get("reload_switch_pass") is not True or result.get("load_flags") != flags or
            result.get("frame_count") != len(flags)):
        raise RuntimeError("Reload switch failed exact transaction/flag gates")
    if cold:
        if result.get("cold_start_pass") is not True:
            raise RuntimeError("Reload switch did not prove fresh-process forced loading")
    elif (any(result.get(key) is not True for key in
              ("reuse_pass", "reload_pass", "retained_latest_pass")) or
          result.get("reload_expected") != 104 / 256):
        raise RuntimeError("Reload switch failed ignored-pointer/reload/latest-bank gates")
    return result


def check_c_validation(result, mode, text):
    if mode == "quality":
        calls = re.findall(r"^EXP_RELOAD_IMAGE (\w+) load=([01])$", text, re.MULTILINE)
        expected = ["baboon", "barbara", "bridge", "coastguard", "face", "flowers", "foreman",
                    "lenna", "man", "monarch", "pepper", "ppt3", "zebra"]
        delta = number(result.get("delta_psnr"))
        if (result.get("csim_pass") is not True or result.get("bit_exact") is not True or
                result.get("reload_switch_quality_pass") is not True or result.get("image_count") != 13 or
                result.get("parameter_reuse_images") != 12 or delta is None or delta < -.1 or
                calls != list(zip(expected, ["1"] + ["0"] * 12))):
            raise RuntimeError("Reload switch failed complete13-image loaded/reused quality gates")
    elif mode in {"sequence", "cold"}:
        check_c_sequence(result, cold=mode == "cold")
    elif mode != "regression":
        raise RuntimeError("Unknown reload-switch validation mode")


def check_rtl_metrics(text, parent):
    matches = re.findall(r"EXP_METRICS (\{[^\r\n]+\})", text)
    if len(matches) != 2:
        raise RuntimeError("Need separate C and RTL reload-switch checks")
    results = [check_c_sequence(json.loads(match)) for match in matches]
    expected_border = number(parent.get("border_mse"))
    if expected_border is None or any(result.get("border_mse") != expected_border for result in results):
        raise RuntimeError("Reload-switch butterfly border differs from frozen parent")
    return results[-1]


def parse_transactions(text, expected=4):
    rows = []
    for line in text.splitlines():
        match = re.fullmatch(r"\s*transaction\s+(\d+):\s+(\d+)\s+(\d+|x)\s*", line)
        if match:
            rows.append({"transaction": int(match[1]), "latency_cycles": int(match[2]),
                         "interval_cycles": None if match[3] == "x" else int(match[3])})
    if len(rows) != expected or [row["transaction"] for row in rows] != list(range(expected)):
        raise RuntimeError("Missing or duplicated per-transaction RTL cycle evidence")
    if any(row["latency_cycles"] <= 0 for row in rows):
        raise RuntimeError("Nonpositive RTL transaction latency")
    if any(row["interval_cycles"] is None or row["interval_cycles"] <= 0 for row in rows[:-1]):
        raise RuntimeError("Missing positive intervals between RTL transactions")
    if rows[-1]["interval_cycles"] is not None:
        raise RuntimeError("Unexpected interval after the final RTL transaction")
    if rows[1]["latency_cycles"] > rows[0]["latency_cycles"] or rows[3]["latency_cycles"] > rows[2]["latency_cycles"]:
        raise RuntimeError("Skipped-load latency exceeds the corresponding loaded call")
    return rows
