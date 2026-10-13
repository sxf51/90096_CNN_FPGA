"""Final OOC feasibility from routed timing, route status and utilization."""
import re
from run_exp import number

CAPS = {"impl_LUT": 81984, "impl_FF": 163968, "impl_DSP": 1248,
        "impl_BRAM18K": 288, "impl_URAM": 64}


def parse_route_status(text):
    result = {}
    patterns = {"impl_unrouted_nets": r"Number of Unrouted Nets\s*[=:]\s*(\d+)",
                "impl_partial_nets": r"Number of Partially Routed Nets\s*[=:]\s*(\d+)"}
    for key, pattern in patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            result[key] = int(matches[-1])
    final = re.findall(r"impl run complete:.*?number of unrouted nets=(\d+)", text)
    if final:
        result["impl_unrouted_nets"] = int(final[-1])
    return result


def evaluate_route(observed):
    result = dict(observed)
    if number(result.get("impl_BRAM36")) is not None:
        result["impl_BRAM18K"] = 2 * number(result["impl_BRAM36"])
    required = {"impl_WNS_ns", "impl_TNS_ns", "impl_WHS_ns", "impl_unrouted_nets", *CAPS}
    missing = sorted(key for key in required if number(result.get(key)) is None)
    result["route_gate_missing"] = missing
    result["route_dsp_over_90pct"] = (number(result.get("impl_DSP")) > .9 * CAPS["impl_DSP"]
                                        if number(result.get("impl_DSP")) is not None else None)
    if missing:
        result["route_feasible"] = None
        return result
    timing = (result["impl_WNS_ns"] >= 0 and result["impl_TNS_ns"] == 0 and
              result["impl_WHS_ns"] >= 0 and result["impl_unrouted_nets"] == 0 and
              number(result.get("impl_partial_nets", 0)) == 0)
    result["timing_met"] = timing
    result["route_feasible"] = timing and all(result[key] <= cap for key, cap in CAPS.items())
    result["route_gate_failures"] = (["setup/hold/route status"] if not timing else []) + [
        key for key, cap in CAPS.items() if result[key] > cap]
    return result


def archive_route_evidence(archive):
    from verify_exp import parse_verification
    observed, _ = parse_verification(archive, "impl")
    for filename in ("impl.log.txt", "impl.log"):
        path = archive / filename
        if path.is_file():
            observed.update(parse_route_status(path.read_text(errors="replace")))
            break
    return evaluate_route(observed)
