"""Matched-noise generated vibration control."""

import numpy as np

from lll.esa_motion_error_controls import make_control
from lll.esa_paired_vibration_control import POLICY, tasks, evaluate
from lll import esa_paired_vibration_control as paired
from lll.studies.artifacts import encoded


def test_same_seed_keeps_all_error_draws_when_vibration_changes():
    off = make_control(duration_s=2, rate_hz=10, seed=2026112100,
                       vibration=False, errors=True)
    on = make_control(duration_s=2, rate_hz=10, seed=2026112100,
                      vibration=True, errors=True)
    for key in ('gyro_white_rads', 'force_white_mps2', 'gyro_bias_rads',
                'force_bias_mps2', 'coupled_gyro_rads',
                'coupled_force_mps2', 'receiver_error_neu_m'):
        np.testing.assert_array_equal(off[key], on[key])
    assert not np.array_equal(off['truth_gyro_body_rads'],
                              on['truth_gyro_body_rads'])


def test_fixed_pairs_use_fresh_seeds_and_finite_allowance():
    selected = tasks()
    assert [row['payload']['seed'] for row in selected] == list(
        range(2026112100, 2026112116))
    assert len(selected) == 16
    assert POLICY['maximum_imu_packets_per_pair'] == 24000
    assert POLICY['original_reads'] == POLICY['protected_reads'] == 0


def test_each_pair_saves_both_forecasts_before_later_scores(tmp_path):
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
            if name == 'forecasts.json':
                assert len(payload) == 2
                assert all(not row['later_receiver_positions_used']
                           for row in payload)

    context = Context()
    result = evaluate(tasks()[0], context)
    assert result['passed'] is True
    assert result['scientific_decision'] == 'abstain'
    assert context.names == ['forecasts.json', 'outcomes.json']


def test_definition_freezes_finite_paired_study(tmp_path):
    name = paired.write_definition(tmp_path)
    assert name == paired.HERE+'/definition.json'
    definition = __import__('json').loads((tmp_path/name).read_bytes())
    assert definition['id'] == paired.ID
    assert definition['workers'] == definition['threads'] == 1
    assert definition['maximum_wall_s'] == 900
    assert len(definition['tasks']) == 16
    assert paired.write_definition(tmp_path) == name
