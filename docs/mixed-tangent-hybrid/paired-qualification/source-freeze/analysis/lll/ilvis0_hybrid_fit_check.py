# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare sealed matched fit forecasts without running a fitter."""
import math


CASE_KEYS = ('model', 'latitude_deg', 'profile', 'policy_id', 'start')


def compare(reference, candidate, reference_binding, candidate_binding,
            reference_errors, candidate_errors, *, tolerance_m=0.01,
            reference_scoring_sha256=None, candidate_scoring_sha256=None):
    """Gate prediction equivalence in metres for one unchanged generated case."""
    if not isinstance(reference, dict) or not isinstance(candidate, dict) or any(
            reference.get(key) != candidate.get(key) for key in CASE_KEYS):
        raise ValueError('same declared case required')
    if not isinstance(reference_binding, dict) or reference_binding != candidate_binding:
        raise ValueError('same frozen inputs required')
    if (reference_scoring_sha256 is not None or candidate_scoring_sha256 is not None) and (
            not isinstance(reference_scoring_sha256, str)
            or reference_scoring_sha256 != candidate_scoring_sha256):
        raise ValueError('same withheld truth required')
    if not math.isfinite(tolerance_m) or tolerance_m <= 0:
        raise ValueError('positive frozen prediction tolerance required')
    costs = (reference.get('training_cost'), candidate.get('training_cost'))
    if any(type(cost) not in (float, int) or not math.isfinite(cost) or cost < 0
           for cost in costs):
        raise ValueError('finite nonnegative cost required')
    if (not isinstance(reference_errors, list) or not isinstance(candidate_errors, list)
            or not reference_errors or len(reference_errors) != len(candidate_errors)):
        raise ValueError('matched finite forecast series required')
    separations = []
    for left, right in zip(reference_errors, candidate_errors, strict=True):
        if (not isinstance(left, list) or not isinstance(right, list)
                or len(left) != 3 or len(right) != 3
                or any(type(value) not in (float, int) or not math.isfinite(value)
                       for value in left + right)):
            raise ValueError('matched finite forecast series required')
        separations.append(math.hypot(*(a - b for a, b in zip(left, right, strict=True))))
    maximum = max(separations)
    fit_gate = all(row.get('converged') is True and row.get('passed') is True
                   and row.get('all_columns_retained') is True
                   for row in (reference, candidate))
    return dict(passed=fit_gate and maximum <= tolerance_m,
                both_fits_adequate=fit_gate,
                forecast_epochs=len(separations),
                maximum_prediction_difference_m=maximum,
                tolerance_m=tolerance_m,
                training_cost_difference=abs(costs[0] - costs[1]))
