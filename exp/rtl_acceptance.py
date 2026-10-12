"""Keep original verdicts separate from explicitly authorized cycle acceptance."""
from run_exp import number


LOWER_BOUND_FAILURE = "Measured RTL cycles are below the preplanned acceptance bound"


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
