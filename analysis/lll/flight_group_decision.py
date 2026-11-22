# SPDX-License-Identifier: AGPL-3.0-or-later
"""Combine externally calibrated candidate tests on a frozen flight cohort."""

import math
from numbers import Real


ROTATING = 'sphere_rotating'
STILL = 'sphere_still'
DISC = 'flat_still'
MODELS = frozenset((ROTATING, STILL, DISC))
LABELS = ('globe', 'disc', 'specified', 'zero')


def _probability(value):
    return (isinstance(value, Real) and not isinstance(value, bool)
            and math.isfinite(value) and 0.0 <= value <= 1.0)


def _within_group(row):
    status = row.get('status')
    if status in ('technical_failure', 'abstain', 'missing'):
        if set(row) != {'status'}:
            raise ValueError('unavailable groups cannot contribute candidate scores')
        return dict.fromkeys(LABELS, 1.0)
    if status != 'complete' or set(row) != {'status', 'p_values', 'adequate'}:
        raise ValueError('explicit group status and complete candidate records required')
    p, adequate = row['p_values'], set(row['adequate'])
    if set(p) != MODELS or not all(_probability(x) for x in p.values()) or not adequate <= MODELS:
        raise ValueError('calibrated candidate p-values and explicit adequacy flags required')
    return dict(
        globe=p[DISC] if adequate & {ROTATING, STILL} else 1.0,
        disc=max(p[ROTATING], p[STILL]) if DISC in adequate else 1.0,
        specified=max(p[DISC], p[STILL]) if ROTATING in adequate else 1.0,
        zero=max(p[DISC], p[ROTATING]) if STILL in adequate else 1.0)


def _decision_from_passes(passes):
    shape_support = [label for label in ('globe', 'disc') if passes[label]]
    shape = shape_support[0] if len(shape_support) == 1 else 'abstain'
    field_support = [label for label in ('specified', 'zero') if passes[label]]
    field = field_support[0] if shape == 'globe' and len(field_support) == 1 else 'abstain'
    return shape, field


def assess(group_ids, results, *, minimum_groups, alpha):
    """Test evidence in at least the declared number of distinct groups.

    Input p-values must each be valid for one physical candidate for the
    whole flight group, including within-group selection and error-law
    uncertainty. Dependence between groups is allowed. Missing scores and
    inadequate alternatives only make the test more conservative. The
    same cohort, group count and significance level apply to both stages.
    """
    groups = tuple(group_ids)
    if (not groups or any(not isinstance(group, str) or not group for group in groups)
            or len(set(groups)) != len(groups) or not set(results) <= set(groups)
            or type(minimum_groups) is not int or not 1 <= minimum_groups <= len(groups)
            or not _probability(alpha) or not 0.0 < alpha < 1.0):
        raise ValueError('distinct frozen group identities and valid shared decision limits required')
    rows = {group: results.get(group, {'status': 'missing'}) for group in groups}
    evidence = {group: _within_group(row) for group, row in rows.items()}
    multiplier = len(groups) - minimum_groups + 1
    tests = {}
    for label in LABELS:
        values = {group: float(evidence[group][label]) for group in groups}
        ordered = sorted(values.values())
        # Under the null at least multiplier groups have valid null
        # p-values. The r-th smallest can only cross a cutoff if at least
        # one of those null groups crosses it too.
        combined = min(1.0, multiplier * ordered[minimum_groups - 1])
        tests[label] = dict(p_value=combined, passes=combined <= alpha,
                           qualifying_groups=[group for group, value in values.items()
                                              if multiplier * value <= alpha])
    shape, field = _decision_from_passes({label: row['passes'] for label, row in tests.items()})
    return dict(version='group-partial-conjunction-v1', shape=shape, field=field,
                cohort=list(groups), minimum_groups=minimum_groups, alpha=float(alpha),
                group_status={group: row['status'] for group, row in rows.items()},
                group_evidence=evidence, tests=tests,
                validity_requires_calibrated_group_inputs=True)
