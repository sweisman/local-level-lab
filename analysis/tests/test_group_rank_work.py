# SPDX-License-Identifier: AGPL-3.0-or-later
from itertools import product

import pytest

from lll.group_rank_calibration import calibrate_candidate
from lll.group_rank_work import candidate_rank_work


@pytest.mark.parametrize('alpha,multiplier', [(.05, 5), (.25, 1), (.5, 1)])
@pytest.mark.parametrize('target', [0., 2.])
def test_rank_bounds_agree_with_every_possible_completion(alpha, multiplier, target):
    draws = tuple('abcd')
    plan = {'nominal': draws, 'stress': draws}
    targets = {'nominal': target, 'stress': 2.}
    for prefix in product((0., 2., None), repeat=2):
        saved = {'nominal': dict(zip(draws, prefix)), 'stress': dict.fromkeys(draws, 0.)}
        audit = candidate_rank_work(
            plan, saved, targets, target_id='test', group_count=multiplier,
            minimum_groups=1, alpha=alpha,
        )
        possible = []
        for rest in product((0., 2., None), repeat=2):
            completed = {**saved, 'nominal': dict(zip(draws, prefix + rest))}
            rank = calibrate_candidate(plan, completed, targets, target_id='test')
            possible.append(rank['p_value'])
        assert audit['p_value_min'] == min(possible)
        assert audit['p_value_max'] == max(possible)
        can_reject = [multiplier * p <= alpha for p in possible]
        expected = ('reject' if all(can_reject) else 'retain' if not any(can_reject)
                    else 'undetermined')
        assert audit['status'] == expected
        assert audit['pending_draws'] == 2


def test_frozen_budget_and_unavailable_target():
    plan = {'null': tuple(str(i) for i in range(199))}
    saved = {'null': {str(i): 0. for i in range(198)}}
    parameters = dict(target_id='test', group_count=7, minimum_groups=3, alpha=.05)
    complete_enough = candidate_rank_work(plan, saved, {'null': 1.}, **parameters)
    assert complete_enough['status'] == 'reject'
    assert complete_enough['p_value_max'] == .01
    assert complete_enough['pending_draws'] == 1
    missing_target = candidate_rank_work(plan, saved, {}, **parameters)
    assert missing_target['status'] == 'retain'
    assert missing_target['p_value_min'] == missing_target['p_value_max'] == 1.
    saved['null'].update({'0': None, '1': 1.})
    too_many_extreme = candidate_rank_work(plan, saved, {'null': 1.}, **parameters)
    assert too_many_extreme['status'] == 'retain'
    assert too_many_extreme['p_value_min'] == .015


def test_rejects_invalid_decision_rule():
    with pytest.raises(ValueError):
        candidate_rank_work({'null': ('a',)}, {}, {}, target_id='test',
                            group_count=7, minimum_groups=8, alpha=.05)
