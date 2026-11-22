"""Frozen fresh-cohort validation and flight-level counting controls."""

from lll.esa_integrated_drift_v2_validation import (
    POLICY, tasks, failure_upper_bound, evaluate)
from lll.esa_integrated_drift_v2_pilot import POLICY as PILOT
from lll.studies.artifacts import encoded


def test_independent_strata_and_finite_allowance():
    selected = tasks()
    assert len(selected) == 256
    assert [task['payload']['seed'] for task in selected] == list(
        range(2026111800, 2026112056))
    assert not set(POLICY['seeds']) & set(PILOT['seeds'])
    assert sum(task['payload']['vibration'] for task in selected) == 128
    assert all(task['limits']['native_calls'] == 0 for task in selected)
    assert POLICY['simultaneous_95_z'] == PILOT['simultaneous_95_z']


def test_exact_joint_confidence_gate_has_a_fixed_boundary():
    assert failure_upper_bound(1, 128, .025) < .05
    assert failure_upper_bound(2, 128, .025) > .05


def test_worker_seals_forecast_before_scoring(tmp_path):
    path = tmp_path/'policy.json'
    path.write_bytes(encoded(POLICY))

    class Context:
        def __init__(self):
            self.names = []
        def input_path(self, key):
            assert key == 'policy'
            return path
        def save(self, name, payload):
            self.names.append(name)
            if name == 'conditional-forecast.json':
                assert payload['later_receiver_positions_used'] is False

    context = Context()
    outcome = evaluate(tasks()[0], context)
    assert outcome['passed'] is True
    assert context.names == ['conditional-forecast.json', 'outcome.json']
    assert outcome['scientific_decision'] == 'abstain'
