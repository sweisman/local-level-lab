# SPDX-License-Identifier: AGPL-3.0-or-later
"""Generated aircraft comparison with both bounded intervals sealed before truth."""


def _score(bounded, observed, cut):
    import numpy as np
    from .ilvis0_precision_value import longitude_residual
    values = np.asarray(observed, dtype=float)[cut:].copy()
    lower = np.asarray(bounded['lower'], dtype=float).reshape(-1, 3)
    upper = np.asarray(bounded['upper'], dtype=float).reshape(-1, 3)
    if (values.shape != lower.shape or upper.shape != lower.shape or
            not np.all(np.isfinite(values)) or
            np.any(lower >= upper)):
        raise ValueError('complete matched withheld target and interval required')
    center = (lower + upper) / 2
    values[:, 1] = center[:, 1] + longitude_residual(
        values[:, 1] - center[:, 1])
    counts = np.sum((lower <= values) & (values <= upper), axis=0)
    return dict(epochs=len(values), marginal_covered=counts.astype(int).tolist(),
                marginal_total=3*len(values),
                median_width_by_axis=np.median(upper-lower, axis=0).tolist(),
                nonlinear_coverage_established=False,
                scientific_decision='abstain')


def calculate(spec, recipe, *, material, factory, kernel_factory, reserve,
              reserve_construction, save, truth, check_continue):
    """Fit a known-law case while preserving the exact withheld-data order."""
    import numpy as np
    from .airquantumgrav_dual_target_prediction import calculate as dual_target
    from .airquantumgrav_prediction import train_and_forecast
    from .bounded_forecast_wrapper import evaluate as bounded_evaluate
    from .ilvis0_native_error_training import ForecastErrorDiagnostic

    if not all(callable(item) for item in
               (kernel_factory, reserve, reserve_construction,
                save, truth, check_continue)):
        raise ValueError('complete generated study callbacks required')
    recorded = {}
    withheld = {}

    def recorded_save(name, value):
        if name in recorded:
            raise ValueError('unique generated artifact required')
        save(name, value)
        recorded[name] = value

    def guarded_truth(times):
        if not {'forecast.json', 'forecast-error-diagnostic.json',
                'receiver-error-diagnostic.json', 'bounded-physical.json',
                'bounded-receiver.json'} <= recorded.keys():
            raise ValueError('both bounded targets and base forecasts required before truth')
        answer = truth(times)
        withheld['physical'] = answer
        return answer

    diagnostic_args = dict(
        receiver_transform_policy=recipe['receiver_transform_policy'],
        bound_margin=recipe['bound_margin'],
        rank_rtol=recipe['rank_rtol'],
        estimability_rtol=recipe['estimability_rtol'],
        estimability_atol=recipe['estimability_atol'])
    physical = ForecastErrorDiagnostic(factory, target='physical_position',
                                       **diagnostic_args)
    receiver = ForecastErrorDiagnostic(factory, target='receiver_measurement',
                                       **diagnostic_args)

    def wrapped(base):
        def run(problem, point, forecast, *, theta, dv, dt, times, reserve):
            return bounded_evaluate(
                base, problem, point, forecast,
                theta=theta, dv=dv, dt=dt, times=times, reserve=reserve,
                save=recorded_save,
                calibration_alpha=recipe['calibration_alpha'],
                future_alpha=recipe['future_alpha'],
                rank_rtol=recipe['rank_rtol'])
        return run

    result = dual_target(
        spec, recipe, material=material,
        train_and_forecast=train_and_forecast,
        kernel_factory=kernel_factory,
        reserve=reserve, reserve_construction=reserve_construction,
        save=recorded_save, truth=guarded_truth,
        check_continue=check_continue, training_error_factory=factory,
        physical_diagnostic=wrapped(physical),
        receiver_diagnostic=wrapped(receiver))
    if 'physical' not in withheld or 'later-receiver-report.json' not in recorded:
        raise ValueError('both later targets must be scored after forecasts')
    cut = material['training_epochs']
    receiver_rows = recorded['later-receiver-report.json']['rows']
    receiver_coordinates = np.array([
        [np.radians(row['latitude_deg']), np.radians(row['longitude_deg']),
         row['height_m']] for row in receiver_rows])
    bounded = dict(
        physical_position=_score(recorded['bounded-physical.json'],
                                 withheld['physical']['coordinates'], cut),
        receiver_measurement=_score(recorded['bounded-receiver.json'],
                                    receiver_coordinates, cut),
        both_bounds_saved_before_later_truth=True,
        calibration_law_known_in_generator=True,
        nonlinear_coverage_established=False,
        scientific_decision='abstain')
    recorded_save('bounded-scores.json', bounded)
    return dict(result, bounded=bounded)
