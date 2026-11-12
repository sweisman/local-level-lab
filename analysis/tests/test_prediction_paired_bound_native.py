"""Two real native fits seal matched bounded forecasts before later truth."""
import pytest
from test_native_structured_training import training_kernels


@pytest.mark.parametrize('truth_law', ['increment', 'point'])
@pytest.mark.parametrize('sensor_case', ['interior', 'z_gyro_boundary'])
def test_native_paired_bounds_use_one_history_and_open_truth_last(
        training_kernels, truth_law, sensor_case):
    from lll.airquantumgrav_noisy_inputs import construct
    from lll.ilvis0_wide_tangent import load
    from lll.prediction_paired_bound_native import calculate
    from lll.prediction_paired_law_study import recipe

    kernels = training_kernels
    r = dict(recipe(), duration_s=2., rate_hz=200, queries=9,
             query_start_s=.1, query_step_s=.2,
             maximum_evaluations=8, calibration_alpha=.025,
             future_alpha=.025)
    spec = dict(model='sphere_rotating', latitude_deg=55.,
                profile=False, start=0, policy_id='reported-short-v1')
    material = construct(spec, dict(r, noise=r['noise_by_law'][truth_law],
                                    sensor_case=sensor_case),
                         reserve=lambda **work: None)
    saved = {}
    events = []
    charges = []

    def save(name, value):
        assert name not in saved
        saved[name] = value
        events.append(name)

    def tangent(anchor):
        native, metadata = load(
            kernels['directory'], gravity_anchor_height_m=anchor,
            expected_source_sha256=kernels['hashes']['analysis/lll/ilvis0_tangent.cpp'])
        return None, native, dict(tangent=metadata)

    def truth():
        events.append('truth')
        assert {'union-bounded-physical.json',
                'union-bounded-receiver.json'} <= saved.keys()
        return dict(opened=True)

    result = calculate(spec, r, material,
                       noise_kernel=kernels['kernel'],
                       kernel_factory=tangent,
                       reserve=lambda **work: charges.append(work),
                       save=save, withheld_truth=truth,
                       check_continue=lambda: None)
    assert result['withheld_truth']['opened']
    assert result['bounded_law_family']['physical_position']['selected_law'] is None
    assert result['bounded_law_family']['receiver_measurement']['candidate_laws'] == [
        'increment', 'point']
    assert result['candidates']['increment']['binding'] == result['candidates']['point']['binding']
    assert events.index('union-bounded-receiver.json') < events.index('truth')
    for law in r['input_laws']:
        assert (saved[law+'/bounded-physical.json']['error_operator_configuration'] ==
                result['candidates'][law]['physical_diagnostic']['error_operator']['operator_configuration'])
        assert (saved[law+'/bounded-receiver.json']['error_operator_configuration'] ==
                result['candidates'][law]['diagnostic']['error_operator']['operator_configuration'])
    assert charges
