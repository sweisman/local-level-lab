"""The weighting control keeps receiver scoring outside its fitted task."""
import pytest


def test_weighting_control_has_one_fixed_receiver_only_task():
    from lll.esa_weighting_control_study import tasks

    rows = tasks()
    assert len(rows) == 1
    assert rows[0]['identity'] == 'linear-points-receiver-only'
    assert rows[0]['payload'] == dict(model='sphere_rotating', profile=False,
                                      policy_id='reported-short-v1', start=0,
                                      method='linear_points')
    assert rows[0]['limits']['native_calls'] == 201
    assert rows[0]['limits']['packet_visits'] == 45_000_000_000


def test_weighting_control_rejects_scoring_as_worker_input():
    from lll.esa_weighting_control_study import accepted_input_keys

    assert 'scoring' not in accepted_input_keys()
    with pytest.raises(ValueError, match='training-only'):
        accepted_input_keys(['interval', 'training', 'scoring'])


def test_weighting_control_needs_source_bound_qualification(tmp_path):
    from lll.esa_weighting_control_study import prepare

    with pytest.raises(ValueError, match='qualification required'):
        prepare(tmp_path)


def test_weighting_control_preserves_failed_accuracy_as_abstention():
    from lll.esa_weighting_control_study import technical_gate

    assert technical_gate(converged=True, forecast_complete=True)
    assert not technical_gate(converged=False, forecast_complete=True)
    assert not technical_gate(converged=True, forecast_complete=False)
