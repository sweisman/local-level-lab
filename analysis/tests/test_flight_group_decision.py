# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


ROTATING, STILL, DISC = ('sphere_rotating', 'sphere_still', 'flat_still')


def complete(rotating, still, disc, adequate):
    return dict(status='complete', p_values=dict(zip((ROTATING, STILL, DISC),
        (rotating, still, disc), strict=True)), adequate=adequate)


def test_shape_and_field_require_the_predeclared_number_of_same_groups():
    from lll.flight_group_decision import assess

    groups = ('a', 'b', 'c', 'd')
    rows = {
        'a': complete(.8, .01, .005, [ROTATING]),
        'b': complete(.7, .8, .005, [ROTATING]),
        'c': complete(.8, .004, .3, [ROTATING]),
        'd': dict(status='technical_failure'),
    }
    out = assess(groups, rows, minimum_groups=2, alpha=.05)
    assert (out['shape'], out['field']) == ('globe', 'abstain')
    assert out['tests']['globe']['p_value'] == pytest.approx(.015)
    assert out['tests']['specified']['qualifying_groups'] == ['a']
    assert out['group_status']['d'] == 'technical_failure'
    rows['c']['p_values'][DISC] = .006
    assert assess(groups, rows, minimum_groups=2, alpha=.05)['field'] == 'specified'


def test_disc_must_exclude_both_globes_in_the_same_groups():
    from lll.flight_group_decision import assess

    rows = {
        'a': complete(.001, .6, .9, [DISC]),
        'b': complete(.001, .6, .9, [DISC]),
        'c': complete(.6, .001, .9, [DISC]),
        'd': complete(.6, .001, .9, [DISC]),
    }
    answer = assess(tuple(rows), rows, minimum_groups=2, alpha=.05)
    assert (answer['shape'], answer['field']) == ('abstain', 'abstain')


def test_missing_groups_stay_in_denominator_and_adequacy_cannot_exclude():
    from lll.flight_group_decision import assess

    groups = ('a', 'b', 'c', 'd')
    rows = {'a': complete(.5, .01, .02, [ROTATING]),
            'b': complete(.5, .01, .02, [ROTATING]),
            'c': complete(.5, .01, 0., [])}
    answer = assess(groups, rows, minimum_groups=2, alpha=.05)
    assert answer['shape'] == 'abstain'
    assert answer['tests']['globe']['p_value'] == pytest.approx(.06)
    assert answer['group_status']['d'] == 'missing'
    assert answer['group_evidence']['c']['globe'] == 1.


def test_contradictory_field_or_shape_support_abstains():
    from lll.flight_group_decision import assess

    groups = ('a', 'b')
    rows = {'a': complete(.9, .001, .001, [ROTATING]),
            'b': complete(.001, .9, .001, [STILL])}
    assert assess(groups, rows, minimum_groups=1, alpha=.05)['field'] == 'abstain'
    rows['b'] = complete(.001, .001, .9, [DISC])
    result = assess(groups, rows, minimum_groups=1, alpha=.05)
    assert (result['shape'], result['field']) == ('abstain', 'abstain')


@pytest.mark.parametrize('groups,rows', [
    (('a', 'a'), {}),
    (('a', 'b'), {'c': dict(status='abstain')}),
    (('a', 'b'), {'a': complete(.1, .2, float('nan'), [DISC])}),
    (('a', 'b'), {'a': complete(.1, .2, .3, ['unknown'])}),
    (('a', 'b'), {'a': dict(status='technical_failure', p_values={})}),
])
def test_unknown_groups_and_bad_statistical_inputs_fail(groups, rows):
    from lll.flight_group_decision import assess

    with pytest.raises(ValueError):
        assess(groups, rows, minimum_groups=2, alpha=.05)


def test_arbitrary_dependence_can_reach_but_not_exceed_the_limit():
    from lll.flight_group_decision import assess

    # Two unrestricted false-null groups and five true-null groups driven by
    # one common discrete uniform. Their 1% events are mutually exclusive.
    count = 0
    groups = tuple('abcdefg')
    for seed in range(1000):
        p_values = [0.0, 0.0] + [((seed + 200*i) % 1000 + 1) / 1000
                                for i in range(5)]
        rows = {key: complete(.8, .8, p, [ROTATING]) for key, p in zip(groups, p_values)}
        count += assess(groups, rows, minimum_groups=3, alpha=.05)['shape'] == 'globe'
    assert count == 50
