# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite-sample reference ranks for externally specified candidate nulls."""

from fractions import Fraction
import math
from numbers import Real


def _valid_id(value):
    return isinstance(value, str) and bool(value)


def _valid_score(value):
    return (isinstance(value, Real) and not isinstance(value, bool)
            and math.isfinite(value) and value >= 0.0)


def calibrate_candidate(planned_draws, saved_scores, target_scores, *, target_id):
    """Conservative upper-tail rank for a complete predeclared null family.

    Each scenario supplies one whole-group statistic per planned draw and
    the target statistic computed by that same procedure. If the null holds
    in one of the declared scenarios, its draws and target must be
    exchangeable under that scenario. The largest rank p-value protects the
    union of the scenario nulls. Missing or failed reference draws never
    lower the result. Unscorable target scenarios return one.
    """
    if (not _valid_id(target_id) or not planned_draws
            or not all(_valid_id(name) for name in planned_draws)
            or not set(saved_scores) <= set(planned_draws)
            or not set(target_scores) <= set(planned_draws)):
        raise ValueError('same declared null scenarios and distinct target identity required')
    results = {}
    for scenario, draw_ids in planned_draws.items():
        draws = tuple(draw_ids)
        if (not all(_valid_id(key) for key in draws) or len(set(draws)) != len(draws)
                or target_id in draws):
            raise ValueError('distinct planned reference draws excluding the target required')
        scores = saved_scores.get(scenario, {})
        target = target_scores.get(scenario)
        if (not set(scores) <= set(draws)
                or any(value is not None and not _valid_score(value) for value in scores.values())
                or (target is not None and not _valid_score(target))):
            raise ValueError('declared draw scores must be finite and nonnegative or unavailable')
        available = [value for value in scores.values() if value is not None]
        missing = len(draws) - len(available)
        extreme = len(draws) if target is None else missing + sum(value >= target for value in available)
        results[scenario] = dict(p_value=(1 + extreme) / (1 + len(draws)),
                                 planned_draws=len(draws), unavailable_draws=missing,
                                 draws_at_least_as_extreme=extreme,
                                 target_available=target is not None)
    return dict(p_value=max(row['p_value'] for row in results.values()),
                by_scenario=results, exchangeability_required=True,
                complete_null_family_required=True)


def minimum_draws(group_count, minimum_groups, *, alpha, unavailable=0):
    """Smallest calibration count that can reach the chosen group cutoff."""
    if (type(group_count) is not int or type(minimum_groups) is not int
            or not 1 <= minimum_groups <= group_count or not _valid_score(alpha)
            or not 0.0 < alpha < 1.0 or type(unavailable) is not int or unavailable < 0):
        raise ValueError('positive cohort, replication requirement and error allowance required')
    cutoff = Fraction(str(alpha)) / (group_count - minimum_groups + 1)
    return math.ceil((unavailable + 1) / cutoff) - 1
