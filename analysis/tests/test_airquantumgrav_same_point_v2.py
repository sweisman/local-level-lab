"""The revised saved-point diagnostic has a finite, unchanged gate."""

import importlib.util
from pathlib import Path


def test_adapter_loads_as_standalone_frozen_file():
    path = Path('analysis/lll/airquantumgrav_same_point_v2.py')
    spec = importlib.util.spec_from_file_location('_frozen_v2_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert len(module.tasks()) == 3


def test_six_calls_have_exact_saved_point_identities_and_limits():
    from lll.airquantumgrav_same_point_v2 import VISITS_PER_CALL, recipe, tasks

    items = tasks()
    assert len(items) == 3
    assert len({item['identity'] for item in items}) == 3
    assert sum(item['limits']['native_calls'] for item in items) == 6
    assert sum(item['limits']['packet_visits'] for item in items) == 6*VISITS_PER_CALL
    assert recipe()['maximum_wall_s'] == 3600.
    assert recipe()['optimizer_starts'] == 0


def test_saved_point_gate_requires_value_and_derivative_improvement():
    from lll.airquantumgrav_same_point_v2 import gate

    old = dict(largest_column=dict(
        maximum_difference_m_per_normalized_unit=1e-6))
    new = dict(values_bitwise_identical=True,
               boundary_counts_identical=True,
               maximum_position_difference_m=0.,
               largest_column=dict(
                   maximum_difference_m_per_normalized_unit=5e-8),
               columns=[
                   dict(name='attitude_x',
                        maximum_difference_m_per_normalized_unit=1e-9),
                   dict(name='attitude_y',
                        maximum_difference_m_per_normalized_unit=2e-9),
                   dict(name='gyro_gain_z',
                        maximum_difference_m_per_normalized_unit=5e-8)])
    assert gate(new, old)
    assert not gate(dict(new, values_bitwise_identical=False), old)
    assert not gate(dict(new, largest_column=dict(
        maximum_difference_m_per_normalized_unit=2e-7)), old)
    changed = dict(new, columns=[dict(name='attitude_x',
                                      maximum_difference_m_per_normalized_unit=1e-7),
                                 *new['columns'][1:]])
    assert not gate(changed, old)
