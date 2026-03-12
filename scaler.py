"""
Scaling Decision Module
───────────────────────
Evaluates SLA constraints against predicted workload
and decides how many containers are required.

SLA thresholds can be overridden at call-time so the
Streamlit dashboard can expose them as interactive sliders.
"""

import math

# ──────────────────────────────────────────────
#  Default SLA Configuration
# ──────────────────────────────────────────────
MAX_CPU_UTILIZATION = 80          # percent
MAX_REQUESTS_PER_CONTAINER = 100  # requests a single container can handle


# ──────────────────────────────────────────────
#  SLA evaluation
# ──────────────────────────────────────────────
def evaluate_sla(
    predicted_requests: int,
    current_cpu: float,
    max_cpu: float = MAX_CPU_UTILIZATION,
    max_reqs: int = MAX_REQUESTS_PER_CONTAINER,
) -> dict:
    """
    Check whether the predicted workload violates SLA constraints.

    Parameters
    ----------
    predicted_requests : predicted next-step request count
    current_cpu        : current CPU utilisation %
    max_cpu            : SLA CPU threshold (configurable)
    max_reqs           : max requests per container (configurable)

    Returns
    -------
    dict with:
        sla_violated : bool
        reasons      : list[str]
    """
    reasons = []

    if current_cpu > max_cpu:
        reasons.append(f"CPU usage {current_cpu:.1f}% exceeds {max_cpu:.0f}%")

    needed = _containers_needed(predicted_requests, max_reqs)
    if needed > 1:
        reasons.append(
            f"Predicted load {predicted_requests} reqs requires {needed} containers"
        )

    return {
        "sla_violated": len(reasons) > 0,
        "reasons": reasons,
    }


# ──────────────────────────────────────────────
#  Scaling decision
# ──────────────────────────────────────────────
def decide_scaling(
    predicted_requests: int,
    current_cpu: float,
    current_containers: int,
    max_cpu: float = MAX_CPU_UTILIZATION,
    max_reqs: int = MAX_REQUESTS_PER_CONTAINER,
) -> dict:
    """
    Decide the scaling action based on the predicted workload.

    Parameters
    ----------
    predicted_requests : predicted next-step request count
    current_cpu        : current CPU utilisation %
    current_containers : number of currently running containers
    max_cpu            : SLA CPU threshold (configurable)
    max_reqs           : max requests per container (configurable)

    Returns
    -------
    dict with:
        action              : "scale_up" | "scale_down" | "no_change"
        required_containers : int
        reason              : str
    """
    required = _containers_needed(predicted_requests, max_reqs)

    # Bump by one extra if CPU is already hot
    if current_cpu > max_cpu:
        required = max(required, current_containers + 1)

    # Never drop below 1 container
    required = max(1, required)

    if required > current_containers:
        action = "scale_up"
        reason = (
            f"Predicted {predicted_requests} reqs -> need {required} containers "
            f"(currently {current_containers})"
        )
    elif required < current_containers:
        action = "scale_down"
        reason = (
            f"Predicted {predicted_requests} reqs -> only {required} containers needed "
            f"(currently {current_containers})"
        )
    else:
        action = "no_change"
        reason = (
            f"Predicted {predicted_requests} reqs -> {required} containers sufficient"
        )

    return {
        "action": action,
        "required_containers": required,
        "reason": reason,
    }


# ──────────────────────────────────────────────
#  Internal helpers
# ──────────────────────────────────────────────
def _containers_needed(predicted_requests: int, max_reqs: int = MAX_REQUESTS_PER_CONTAINER) -> int:
    """Calculate the minimum number of containers for a given load."""
    return max(1, math.ceil(predicted_requests / max_reqs))
