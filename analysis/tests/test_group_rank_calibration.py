# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.flight_group_decision import assess


def test_composite_null_uses_most_compatible_declared_case():
    from lll.group_rank_calibration import calibrate_candidate

    plan = {'nominal': ('a', 'b', 'c'), 'shifted': ('a', 'b', 'c')}
    saved = {'nominal': {'a': 1., 'b': 2., 'c': 3.},
             'shifted': {'a': 2., 'b': 4., 'c': 5.}}
    result = calibrate_candidate(plan, saved, dict(nominal=4., shifted=4.), target_id='test')
    assert result['by_scenario']['nominal']['p_value'] == .25
    assert result['by_scenario']['shifted']['p_value'] == .75
    assert result['p_value'] == .75


def test_failures_are_at_least_as_extreme_and_missing_case_protects_null():
    from lll.group_rank_calibration import calibrate_candidate

    plan = {'one': ('a', 'b', 'c', 'd'), 'two': ('a', 'b', 'c', 'd')}
    result = calibrate_candidate(plan, {'one': {'a': 1., 'b': None}}, {'one': 3.}, target_id='test')
    assert result['by_scenario']['one']['p_value'] == .8
    assert result['by_scenario']['one']['unavailable_draws'] == 3
    assert result['by_scenario']['two']['p_value'] == 1.
    assert result['p_value'] == 1.


def test_exact_exchangeable_ranks_remain_conservative_with_ties_and_failures():
    from lll.group_rank_calibration import calibrate_candidate

    scores = [0., 1., 2., 3., 4., 5., 6., 7., 8., 8.]
    results = []
    for leave_out, target in enumerate(scores):
        plan = [str(i) for i in range(len(scores)) if i != leave_out]
        saved = {i: scores[int(i)] if int(i) != 2 else None for i in plan}
        results.append(calibrate_candidate({'nuisance': plan}, {'nuisance': saved},
            {'nuisance': target}, target_id=str(leave_out))['p_value'])
    for threshold in (.1, .2, .3, .4, .6, 1.):
        assert sum(p <= threshold for p in results) <= threshold * len(scores)


@pytest.mark.parametrize('plan,scores,target', [
    ({'a': ['same']}, {}, {}),
    ({'a': ['seed', 'seed']}, {}, {}),
    ({'a': ['seed']}, {'unknown': {}}, {}),
    ({'a': ['seed']}, {'a': {'other': 3.}}, {}),
    ({'a': ['seed']}, {'a': {'seed': float('nan')}}, {}),
    ({'a': ['seed']}, {'a': {'seed': 1.}}, {'a': -1.}),
])
def test_unknown_or_reused_draws_are_rejected(plan, scores, target):
    from lll.group_rank_calibration import calibrate_candidate

    with pytest.raises(ValueError):
        calibrate_candidate(plan, scores, target, target_id='same')


def test_rank_resolution_matches_flight_rule_and_worsens_with_failures():
    from lll.group_rank_calibration import minimum_draws, calibrate_candidate

    groups = tuple('abcdefg')
    assert minimum_draws(len(groups), 3, alpha=.05) == 99
    assert minimum_draws(len(groups), 3, alpha=.05, unavailable=1) == 199
    for draws, accepted in [(98, False), (99, True)]:
        plan = tuple(str(i) for i in range(draws))
        rows = {}
        for group in groups[:3]:
            disc_p = calibrate_candidate({'null': plan}, {'null': dict.fromkeys(plan, .1)},
                {'null': 1.}, target_id=group)['p_value']
            rows[group] = dict(status='complete',
                p_values=dict(flat_still=disc_p, sphere_rotating=.8, sphere_still=.8),
                adequate=['sphere_rotating'])
        result = assess(groups, rows, minimum_groups=3, alpha=.05)
        assert (result['shape'] == 'globe') is accepted
