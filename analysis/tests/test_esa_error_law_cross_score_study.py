"""A bounded fixed-point comparison cannot retune from later GPS positions."""

import pytest


def test_cross_score_has_one_fixed_no_fit_task():
    from lll.esa_error_law_cross_score_study import tasks

    rows = tasks()
    assert len(rows) == 1
    assert rows[0]['identity'] == 'two-saved-points-two-objectives'
    assert rows[0]['payload'] == dict(model='sphere_rotating', profile=False,
                                      policy_id='reported-short-v1',
                                      method='linear_points',
                                      optimize=False, forecast=False)
    assert rows[0]['limits']['native_calls'] == 300_000
    assert rows[0]['limits']['packet_visits'] == 1_500_000_000


def test_cross_score_excludes_later_receiver_rows():
    from lll.esa_error_law_cross_score_study import accepted_input_keys

    assert 'scoring' not in accepted_input_keys()
    assert 'saved-increment-forecast' in accepted_input_keys()
    with pytest.raises(ValueError, match='training-only'):
        accepted_input_keys(['training', 'scoring'])


def test_cross_score_requires_source_qualification(tmp_path):
    from lll.esa_error_law_cross_score_study import prepare

    with pytest.raises(ValueError, match='qualification required'):
        prepare(tmp_path)


def test_cross_score_replay_gate_checks_both_originating_costs():
    from lll.esa_error_law_cross_score_study import diagonal_replay_gate

    matrix = dict(receiver_only=dict(receiver_only=681., weighted=500.),
                  weighted=dict(receiver_only=750., weighted=13.))
    expected = dict(receiver_only=681., weighted=13.)
    assert diagonal_replay_gate(matrix, expected) is True
    changed = dict(matrix, weighted=dict(receiver_only=750., weighted=12.))
    assert diagonal_replay_gate(changed, expected) is False
    assert diagonal_replay_gate(matrix, dict(receiver_only=682., weighted=13.)) is False
