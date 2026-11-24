# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction

import pytest


def test_thirteen_missing_reference_seeds_leave_only_unanimous_rule_reachable():
    from lll.prediction_reference_resolution import rank_resolution

    scores = [float(score) for score in range(286)]
    result = rank_resolution(299, scores)
    assert result['smallest_p_value'] == '7/150'
    assert [row['minimum_groups'] for row in result['rules'] if row['reachable']] == [7]
    last = result['rules'][-1]
    assert last['maximum_available_tail_count'] == 1
    assert last['strictly_above_m'] == 284.
    assert last['minimum_planned_if_missing_fixed'] == 279


def test_exact_rank_counts_ties_and_unavailable_seeds():
    from lll.group_rank_calibration import calibrate_candidate
    from lll.prediction_reference_resolution import rank_resolution

    scores = [float(score) for score in range(283)] + [300., 300., 301.]
    result = rank_resolution(299, scores)['rules'][-1]
    planned = {'scenario': [str(i) for i in range(299)]}
    seen = {'scenario': {str(i): value for i, value in enumerate(scores)}}
    at = result['strictly_above_m']
    for offset, verdict in ((0., False), (.01, True)):
        report = calibrate_candidate(planned, seen, {'scenario': at+offset}, target_id='new')
        assert (report['p_value'] <= float(Fraction(result['cutoff']))) is verdict
    assert rank_resolution(299, scores[:-1])['rules'][-1]['maximum_available_tail_count'] == 0
    assert not rank_resolution(299, scores[:-2])['rules'][-1]['reachable']
    with pytest.raises(ValueError, match='finite'):
        rank_resolution(1, [float('nan')])


def test_published_traces_reject_a_start_with_higher_earlier_loss():
    from lll.prediction_reference_resolution import verify_earlier_choices

    stable = dict(draw_seed='11', role='calibration', model='sphere_still', law='point',
                  profile='False', converged='True', complete='True')
    parent = [dict(stable, start='0', identity='first', training_cost='10'),
              dict(stable, start='1', identity='second', training_cost='9')]
    case = dict(seed=11, model='sphere_still', input_law='point', profile=False)
    verify_earlier_choices(parent, [dict(case, earlier_cost=9., start=1, identity='second')])
    with pytest.raises(ValueError, match='earlier-cost'):
        verify_earlier_choices(parent, [dict(case, earlier_cost=10., start=0, identity='first')])
