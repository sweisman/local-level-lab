# SPDX-License-Identifier: AGPL-3.0-or-later
from itertools import product

import pytest

from lll.flight_group_decision import DISC, ROTATING, STILL, assess
from lll.group_cohort_work import cohort_rank_work
from lll.group_rank_work import candidate_rank_work


MODELS = (ROTATING, STILL, DISC)


def brackets(adequate, rotating=(.4, .4), still=(.4, .4), disc=(.4, .4)):
    return dict(status='complete', adequate=adequate,
                ranks={model: dict(p_value_min=lo, p_value_max=hi,
                                  pending_draws=int(lo != hi))
                       for model, (lo, hi) in zip(MODELS, (rotating, still, disc), strict=True)})


def completions(rows, alpha, minimum):
    by_group = []
    for row in rows.values():
        if row['status'] != 'complete':
            by_group.append((row,))
            continue
        alternatives = [(rank['p_value_min'], rank['p_value_max']) for rank in row['ranks'].values()]
        by_group.append(tuple(dict(status='complete', adequate=row['adequate'],
                                   p_values=dict(zip(row['ranks'], values, strict=True)))
                              for values in product(*alternatives)))
    outcomes = set()
    for choices in product(*by_group):
        result = assess(rows, dict(zip(rows, choices, strict=True)), minimum_groups=minimum, alpha=alpha)
        outcomes.add((result['shape'], result['field']))
    return outcomes


@pytest.mark.parametrize('minimum', (1, 2, 3, 4))
def test_possible_decisions_match_every_group_and_candidate_completion(minimum):
    rows = {
        'a': brackets([ROTATING, STILL], rotating=(.005, .4), still=(.01, .4), disc=(.01, .01)),
        'b': brackets([DISC, STILL], rotating=(.01, .4), still=(.01, .01), disc=(.005, .4)),
        'c': brackets([ROTATING, DISC], rotating=(.01, .01), still=(.01, .4), disc=(.005, .4)),
        'd': {'status': 'technical_failure'},
    }
    result = cohort_rank_work(rows, rows, minimum_groups=minimum, alpha=.04)
    expected = completions(rows, .04, minimum)
    assert {(x['shape'], x['field']) for x in result['possible_decisions']} == expected
    assert result['decision_fixed'] is (len(expected) == 1)
    assert (result['conservative']['shape'], result['conservative']['field']) in expected
    assert result['pending_draw_slots'] == 6


def test_joint_vote_constraints_can_fix_field_before_shape():
    rows = {'flight': brackets([DISC, ROTATING], rotating=(.01, .01),
                               still=(.01, .01), disc=(.01, .20))}
    result = cohort_rank_work(rows, rows, minimum_groups=1, alpha=.05)
    assert result['possible_decisions'] == [dict(shape='abstain', field='abstain'),
                                            dict(shape='disc', field='abstain')]
    assert not result['shape_fixed'] and result['field_fixed']


def test_irrelevant_pending_draws_leave_both_decisions_fixed():
    parameters = dict(group_count=3, minimum_groups=2, alpha=.05)
    plan = {'null': tuple(f'draw-{i}' for i in range(79))}
    shared = {}
    for identity in ('a', 'b', 'c'):
        full = dict.fromkeys(plan['null'], 0.)
        sealed = full if identity != 'c' else {}
        ranks = {model: candidate_rank_work(plan, {'null': sealed},
                {'null': 0. if model == ROTATING else 1.}, target_id=identity, **parameters)
                 for model in MODELS}
        shared[identity] = dict(status='complete', adequate=[ROTATING], ranks=ranks)
    result = cohort_rank_work(shared, shared, minimum_groups=2, alpha=.05)
    assert result['possible_decisions'] == [dict(shape='globe', field='specified')]
    assert result['decision_fixed'] and result['pending_draw_slots'] == 237
    assert result['conservative']['tests']['specified']['qualifying_groups'] == ['a', 'b']
    assert result['conservative']['tests']['specified']['p_value'] == .025


def test_cohort_requires_explicit_terminal_query_states_and_valid_rank_bounds():
    with pytest.raises(ValueError):
        cohort_rank_work(('a', 'b'), {'a': {'status': 'abstain'}}, minimum_groups=1, alpha=.05)
    malformed = {'a': brackets([ROTATING], disc=(.20, .01))}
    with pytest.raises(ValueError):
        cohort_rank_work(malformed, malformed, minimum_groups=1, alpha=.05)
    malformed['a']['ranks'][DISC].update(p_value_min=.005, pending_draws=0)
    with pytest.raises(ValueError):
        cohort_rank_work(malformed, malformed, minimum_groups=1, alpha=.05)
