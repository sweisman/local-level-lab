# SPDX-License-Identifier: AGPL-3.0-or-later
"""Prospective numerical comparison of nearly tied optimizer starts."""

import math

from .ilvis0_start_equivalence import compare_start_sets


def compare_start_sets_v2(reference, candidate, *, relative_cost_tolerance,
                          absolute_cost_tolerance, forecast_tolerance_m):
    """Prospective cost-floor and within-method start-stability check.

    The absolute floor is supplied by a separately justified, frozen caller.
    This helper does not choose one from saved method discrepancies.
    """
    if (type(absolute_cost_tolerance) not in (int, float) or
            not math.isfinite(absolute_cost_tolerance) or
            absolute_cost_tolerance < 0):
        raise ValueError('finite nonnegative absolute cost tolerance required')
    # Reuse the original input, binding, cost and forecast validation without
    # changing the completed first study's rule or outcome.
    checked = compare_start_sets(reference, candidate,
        relative_cost_tolerance=relative_cost_tolerance,
        forecast_tolerance_m=forecast_tolerance_m)
    ref = {row['start']: row for row in reference}
    cand = {row['start']: row for row in candidate}
    ref_primary = checked['reference_primary']
    cand_primary = checked['candidate_primary']

    def close(a, b):
        return abs(a-b) <= (absolute_cost_tolerance +
                             relative_cost_tolerance*max(a, b))

    ref_min = ref[ref_primary]['training_cost']
    cand_min = cand[cand_primary]['training_cost']
    ref_ties = [start for start in sorted(ref)
                if close(ref[start]['training_cost'], ref_min)]
    cand_ties = [start for start in sorted(cand)
                 if close(cand[start]['training_cost'], cand_min)]

    def spread(a, a_starts, b, b_starts):
        value = max(math.dist(p, q)
            for i in a_starts for j in b_starts
            for p, q in zip(a[i]['forecast'], b[j]['forecast'], strict=True))
        if not math.isfinite(value):
            raise ValueError('finite forecast separation required')
        return value

    cross = spread(ref, ref_ties, cand, cand_ties)
    within_ref = spread(ref, ref_ties, ref, ref_ties)
    within_cand = spread(cand, cand_ties, cand, cand_ties)
    cost_agreement = all(close(ref[start]['training_cost'],
                               cand[start]['training_cost']) for start in ref)
    selection_stable = ref_primary in cand_ties and cand_primary in ref_ties
    all_fits_pass = checked['all_fits_pass']
    return dict(version='start-equivalence-v2',
        equivalent=bool(all_fits_pass and selection_stable and cost_agreement
                        and max(cross, within_ref, within_cand)
                            <= forecast_tolerance_m),
        all_fits_pass=all_fits_pass,
        reference_primary=ref_primary, candidate_primary=cand_primary,
        reference_near_ties=ref_ties, candidate_near_ties=cand_ties,
        selection_stable=selection_stable,
        same_start_costs_agree=cost_agreement,
        cross_start_maximum_m=cross,
        reference_within_maximum_m=within_ref,
        candidate_within_maximum_m=within_cand,
        relative_cost_tolerance=relative_cost_tolerance,
        absolute_cost_tolerance=absolute_cost_tolerance,
        forecast_tolerance_m=forecast_tolerance_m,
        forecast_epochs=checked['forecast_epochs'])
