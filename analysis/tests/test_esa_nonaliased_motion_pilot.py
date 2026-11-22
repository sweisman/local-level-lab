"""Receiver-visible motion pilot configuration and forecast order."""

import json

from lll import esa_nonaliased_motion_pilot as pilot
from lll.studies.artifacts import encoded


def test_fresh_finite_pair_set():
    selected = pilot.tasks()
    assert [row['payload']['seed'] for row in selected] == list(
        range(2026112300, 2026112316))
    assert len(selected) == 16
    assert pilot.POLICY['maximum_imu_packets_per_pair'] == 24000
    assert pilot.POLICY['original_reads'] == 0
    assert pilot.POLICY['protected_reads'] == 0


def test_both_earlier_only_forecasts_saved_before_scoring(tmp_path):
    path = tmp_path/'policy.json'
    path.write_bytes(encoded(pilot.POLICY))

    class Context:
        def __init__(self):
            self.names = []
        def input_path(self, key):
            assert key == 'policy'
            return path
        def save(self, name, payload):
            self.names.append(name)
            if name == 'forecasts.json':
                assert len(payload) == 2
                assert all(row['later_receiver_positions_used'] is False
                           for row in payload)
            if name == 'outcomes.json':
                assert payload['matched_error_draws'] is True
                assert len(payload['outcomes']) == 2

    context = Context()
    result = pilot.evaluate(pilot.tasks()[0], context)
    assert context.names == ['forecasts.json', 'outcomes.json']
    assert result['technical_complete'] is True
    assert result['scientific_decision'] == 'abstain'


def test_definition_is_idempotent_and_finite(tmp_path):
    name = pilot.write_definition(tmp_path)
    definition = json.loads((tmp_path/name).read_bytes())
    assert definition['id'] == pilot.ID
    assert definition['workers'] == definition['threads'] == 1
    assert definition['maximum_wall_s'] == 900
    assert len(definition['tasks']) == 16
    assert pilot.HERE+'/PILOT_PLAN.md' in definition['sources']
    assert pilot.write_definition(tmp_path) == name
