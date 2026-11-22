"""The saved observed pilot keeps each failed numerical gate visible."""

from lll import ilvis0_observed_method_diagnosis as diagnosis


def test_probe_gates_are_counted_without_reclassifying_a_fit():
    case = dict(converged=False, probe_reason='fresh_position_probe_not_stable',
                probe_actual_cost_change=2e-8, fresh_stationarity=2e-4,
                position_probe_rms_m=[0.0, 0.0, 0.002],
                position_probe_max_m=[0.0, 0.0, 0.012])
    assert diagnosis.failed_gates(case) == (
        'relative_cost_change', 'fresh_stationarity',
        'position_rms', 'position_maximum')
    assert case['converged'] is False


def test_early_stationarity_and_cost_only_are_distinct():
    early = dict(converged=False, probe_reason='not_stationary')
    cost = dict(converged=False, probe_reason='fresh_position_probe_not_stable',
                probe_actual_cost_change=1.01e-8, fresh_stationarity=1e-7,
                position_probe_rms_m=[0.0] * 3,
                position_probe_max_m=[0.0] * 3)
    assert diagnosis.failed_gates(early) == ('stationarity_before_probe',)
    assert diagnosis.failed_gates(cost) == ('relative_cost_change',)
