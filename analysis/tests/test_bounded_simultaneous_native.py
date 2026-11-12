"""Short native aircraft fit exercises both whole-stretch forecast targets."""
from test_native_structured_training import training_kernels


def test_native_aircraft_fit_seals_both_simultaneous_targets(training_kernels):
    from lll.airquantumgrav_noisy_inputs import construct, error_law
    from lll.airquantumgrav_prediction import train_and_forecast
    from lll.bounded_simultaneous_forecast_wrapper import evaluate
    from lll.ilvis0_native_error_training import (
        ErrorTrainingFactory, ForecastErrorDiagnostic)
    from lll.ilvis0_wide_tangent import load
    from lll.prediction_paired_law_study import recipe

    spec = dict(model='sphere_rotating', latitude_deg=55., profile=False,
                start=0, policy_id='reported-short-v1')
    plan = dict(recipe(), duration_s=2., rate_hz=200, queries=9,
                query_start_s=.1, query_step_s=.2, maximum_evaluations=8,
                calibration_alpha=.025)
    plan['noise'] = plan['noise_by_law']['increment']
    material = construct(spec, plan, reserve=lambda **work: None)
    anchor = material['training_rows'][0]['height_m']
    kernels = training_kernels
    tangent, _ = load(
        kernels['directory'], gravity_anchor_height_m=anchor,
        expected_source_sha256=kernels['hashes']['analysis/lll/ilvis0_tangent.cpp'])
    kernel = None
    factory = ErrorTrainingFactory(
        noise=error_law(plan['noise']), noise_kernel=kernels['kernel'],
        gravity_anchor_height_m=anchor,
        maximum_packets=len(material['dt']), maximum_queries=len(material['times']),
        maximum_bytes=64*1024**2,
        anchor_policy=plan['covariance_anchor_policy'])
    arguments = dict(
        receiver_transform_policy=plan['receiver_transform_policy'],
        bound_margin=plan['bound_margin'], rank_rtol=plan['rank_rtol'],
        estimability_rtol=plan['estimability_rtol'],
        estimability_atol=plan['estimability_atol'])
    diagnostics = {
        target: ForecastErrorDiagnostic(factory, target=target, **arguments)
        for target in ('physical_position', 'receiver_measurement')}
    saved = {}

    def save(name, value):
        assert name not in saved
        saved[name] = value

    def both(*args, **kwargs):
        results = {}
        for target, diagnostic in diagnostics.items():
            results[target] = evaluate(
                diagnostic, *args, **kwargs, save=save,
                calibration_alpha=.025, simultaneous_alpha=.05,
                rank_rtol=plan['rank_rtol'])
        return results['physical_position']

    result = train_and_forecast(
        **{key:material[key] for key in ('theta', 'dv', 'dt')},
        times=material['times'], training_rows=material['training_rows'],
        time_origin_s=0., model=spec['model'], profile=spec['profile'],
        policy_id=spec['policy_id'], start=spec['start'],
        limits=plan['limits'], maximum_evaluations=plan['maximum_evaluations'],
        maximum_interval_s=1.5/plan['rate_hz'], kernel=kernel,
        tangent_kernel=tangent, reserve=lambda **work: None, save=save,
        check_continue=lambda: None, training_error_factory=factory,
        forecast_error_diagnostic=both, clock=plan['clock'])
    assert 'forecast' in result
    for target, name in (
            ('physical_position', 'simultaneous-bounded-physical.json'),
            ('receiver_measurement', 'simultaneous-bounded-receiver.json')):
        interval = saved[name]
        assert interval['prediction_target'] == target
        assert interval['coordinate_count'] == 3*interval['prediction_epochs']
        assert interval['affine_conditional_simultaneous_lower_bound'] == .95
        assert interval['later_observations_used'] is False
        assert interval['simultaneous_coverage_established'] is False
