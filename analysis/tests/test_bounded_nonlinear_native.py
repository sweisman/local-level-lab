"""A real short native forecast seals both bounded targets before later truth."""
from test_native_structured_training import training_kernels
import pytest


@pytest.mark.parametrize('law', ['increment', 'point'])
@pytest.mark.parametrize('sensor_case', ['interior', 'z_gyro_boundary'])
def test_native_bounded_case_seals_both_targets_before_truth(
        training_kernels, law, sensor_case):
    from lll.airquantumgrav_noisy_inputs import construct, error_law
    from lll.airquantumgrav_observation_truth import receiver_samples
    from lll.airquantumgrav_training_controls import _spec
    from lll.bounded_nonlinear_case import calculate
    from lll.ilvis0_native_error_training import ErrorTrainingFactory
    from lll.ilvis0_wide_tangent import load
    from lll.prediction_aircraft_error_integration import recipe
    k = training_kernels
    r = dict(recipe(), calibration_alpha=.025, future_alpha=.025)
    spec = dict(model='sphere_rotating', latitude_deg=55., profile=False,
                start=0, policy_id='reported-short-v1')
    configured = dict(r, noise=r['noise_by_law'][law],
                      sensor_case=sensor_case, clock='nominal_200Hz')
    material = construct(spec, configured, reserve=lambda **work: None)
    anchor = material['training_rows'][0]['height_m']

    def kernels(height):
        tangent, metadata = load(
            k['directory'], gravity_anchor_height_m=height,
            expected_source_sha256=k['hashes']['analysis/lll/ilvis0_tangent.cpp'])
        return None, tangent, dict(tangent=metadata)

    factory = ErrorTrainingFactory(
        noise=error_law(configured['noise']), noise_kernel=k['kernel'],
        gravity_anchor_height_m=anchor,
        maximum_packets=len(material['dt']),
        maximum_queries=len(material['times']),
        maximum_bytes=64*1024**2,
        anchor_policy=r['covariance_anchor_policy'])
    arguments, sign = _spec({key:value for key,value in spec.items()
                             if key != 'policy_id'})
    saved = {}
    charges = []

    def withheld(times):
        assert {'bounded-physical.json', 'bounded-receiver.json'} <= saved.keys()
        return receiver_samples(times=times, sign=sign, **arguments,
                                height_profile=r['height_profile'],
                                gravity_model=r['gravity_model'])

    result = calculate(
        spec, configured, material=material, factory=factory,
        kernel_factory=kernels, reserve=lambda **work: charges.append(work),
        reserve_construction=lambda **work: None,
        save=lambda name, value: saved.setdefault(name, value),
        truth=withheld, check_continue=lambda: None)
    assert result['bounded']['both_bounds_saved_before_later_truth']
    assert result['bounded']['scientific_decision'] == 'abstain'
    assert saved['bounded-scores.json'] == result['bounded']
    assert result['native_calls'] == sum(row['native_calls'] for row in charges)
