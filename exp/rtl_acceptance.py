"""Keep original verdicts separate from explicitly authorized cycle acceptance."""
from run_exp import number


LOWER_BOUND_FAILURE = "Measured RTL cycles are below the preplanned acceptance bound"


def check_transaction_cycle_limits(config, measured):
    limits = config.get("rtl_transaction_max_cycles")
    if limits is None:
        return
    rows = measured.get("reload_switch_transactions", [])
    if (not config.get("reload_switch_validation") or not isinstance(limits, list) or
            len(limits) != 4 or any(type(value) is not int or value <= 0 for value in limits) or
            len(rows) != 4 or [row.get("transaction") for row in rows] != list(range(4)) or
            [row.get("load_params") for row in rows] != [1, 0, 1, 0]):
        raise RuntimeError("Need four ordered reload transactions and positive preplanned cycle limits")
    for row, limit in zip(rows, limits):
        cycles = row.get("latency_cycles")
        if type(cycles) is not int or cycles <= 0:
            raise RuntimeError("Per-call latency must be a measured positive integer")
        if cycles > limit:
            raise RuntimeError("RTL transaction " + str(row["transaction"]) +
                               " exceeds its preplanned parent+1percent bound: " +
                               str(cycles) + " > " + str(limit))


def accepted_cosim(row, config):
    measured = config.get("verification", {})
    if config.get("operation") != "cosim" or measured.get("rtl_status") != "Pass":
        return False
    if row.get("status") == "cosim_complete":
        return True
    override = config.get("acceptance_override", {})
    cycles = number(measured.get("rtl_latency_max"))
    limit = number(override.get("max_cycles"))
    return (row.get("status") == "fail" and config.get("errors") == [LOWER_BOUND_FAILURE]
            and override.get("authorized_by") == "user"
            and override.get("policy") == "upper_latency_bound_only"
            and bool(override.get("decision_reference"))
            and limit is not None and limit == number(config.get("rtl_max_cycles"))
            and cycles is not None and 0 < cycles <= limit
            and measured.get("changed_params_bit_exact") is True
            and config.get("reload_params") is True)


def acceptance_basis(row, config):
    if not accepted_cosim(row, config):
        return "rejected_or_unmeasured"
    return ("user_authorized_upper_only" if row.get("status") == "fail"
            else "original_verification_pass")
