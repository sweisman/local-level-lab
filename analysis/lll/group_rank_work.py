# SPDX-License-Identifier: AGPL-3.0-or-later
"""Work bounds for a reference-rank test with a fixed flight cohort."""

from .group_rank_calibration import calibrate_candidate, minimum_draws


def candidate_rank_work(planned_draws, sealed_scores, target_scores, *,
                        target_id, group_count, minimum_groups, alpha):
    """Bound the eventual rank with unchanged reference identities and settings.

    A missing key is unfinished. A sealed None is unavailable forever and
    counts as extreme, as does a tie. Target scores must already be sealed.
    The lower bound is for work scheduling only. The upper bound is the
    conservative p-value if all remaining draws are left unavailable.
    """
    minimum_draws(group_count, minimum_groups, alpha=alpha)
    multiplier = group_count - minimum_groups + 1
    current = calibrate_candidate(
        planned_draws, sealed_scores, target_scores, target_id=target_id,
    )
    by_scenario = {}
    for scenario, row in current['by_scenario'].items():
        planned = row['planned_draws']
        pending = planned - len(sealed_scores.get(scenario, {}))
        extreme = row['draws_at_least_as_extreme']
        # Valid scores are nonnegative, so even unfinished draws cannot
        # fall below a zero target.
        if row['target_available'] and target_scores[scenario] > 0:
            extreme -= pending
        by_scenario[scenario] = dict(
            pending_draws=pending,
            p_value_min=(1 + extreme) / (1 + planned),
            p_value_max=row['p_value'],
        )
    lower = max(row['p_value_min'] for row in by_scenario.values())
    upper = current['p_value']
    # Match the floating-point comparison in flight_group_decision.assess
    # at the decision boundary.
    status = 'undetermined'
    if multiplier * upper <= alpha:
        status = 'reject'
    elif multiplier * lower > alpha:
        status = 'retain'
    return dict(
        status=status,
        p_value_min=lower,
        p_value_max=upper,
        pending_draws=sum(row['pending_draws'] for row in by_scenario.values()),
        by_scenario=by_scenario,
    )
