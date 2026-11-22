"""Fresh-cohort range gate; the failed earlier gate is immutable."""

from lll.esa_threshold_42_validation import POLICY, tasks, evaluate
from lll.esa_integrated_drift_v2_validation import (
    POLICY as EARLIER, failure_upper_bound)
from lll.esa_integrated_drift_v2_pilot import POLICY as PILOT
from lll.studies.artifacts import encoded


def test_fresh_fixed_cohort_and_exact_gate():
    selected = tasks()
    assert len(selected) == 256
    assert [row['payload']['seed'] for row in selected] == list(
        range(2026112400, 2026112656))
    assert sum(row['payload']['vibration'] for row in selected) == 128
    assert not set(POLICY['seeds']) & set(EARLIER['seeds'])
    assert not set(POLICY['seeds']) & set(PILOT['seeds'])
    assert POLICY['simultaneous_z'] == 4.2
    assert PILOT['simultaneous_95_z'] < POLICY['simultaneous_z']
    assert all(row['limits']['native_calls'] == 0 for row in selected)
    assert failure_upper_bound(1, 128, .025) < .05
    assert failure_upper_bound(2, 128, .025) > .05


def test_forecast_sealed_before_scoring_and_new_threshold_used(tmp_path):
    path = tmp_path/'policy.json'
    path.write_bytes(encoded(POLICY))

    class Context:
        names = ()

        def input_path(self, key):
            assert key == 'policy'
            return path

        def save(self, name, payload):
            self.names += (name,)
            if name == 'conditional-forecast.json':
                assert payload['later_receiver_positions_used'] is False
            if name == 'outcome.json':
                assert payload['threshold_z'] == 4.2
                assert payload['range_contained'] == (
                    payload['maximum_absolute_standardized_error'] <= 4.2)

    context = Context()
    result = evaluate(tasks()[0], context)
    assert result['passed'] is True
    assert context.names == ('conditional-forecast.json', 'outcome.json')
    assert result['scientific_decision'] == 'abstain'
