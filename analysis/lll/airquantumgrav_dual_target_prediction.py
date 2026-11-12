# SPDX-License-Identifier: AGPL-3.0-or-later
"""Score both future physical position and receiver report after forecasting."""
import json


def _marginal_score(diagnostic, observed, cut):
    import numpy as np
    from lll.ilvis0_precision_value import longitude_residual
    target = diagnostic['prediction_target']
    fixed = diagnostic['fixed_parameters']
    measured = np.asarray(observed, dtype=float)[cut:]
    mean = np.asarray(fixed['mean'], dtype=float)
    covariance = np.asarray(fixed['covariance'], dtype=float)
    if (measured.ndim != 2 or measured.shape[1:] != (3,) or
            mean.shape != measured.shape or
            covariance.shape != (len(measured),3,3) or
            not all(np.all(np.isfinite(x)) for x in (measured,mean,covariance)) or
            np.any(np.diagonal(covariance,axis1=1,axis2=2) <= 0)):
        raise ValueError('finite matched future means and covariance required')
    difference = measured-mean
    difference[:,1] = longitude_residual(difference[:,1])
    sigma = np.sqrt(np.diagonal(covariance,axis1=1,axis2=2))
    covered = np.abs(difference) <= 1.959963984540054*sigma
    return dict(target=target, epochs=len(measured),
                marginal_covered=[int(value) for value in np.sum(covered,axis=0)],
                marginal_total=3*len(measured),
                fixed_calibration_only=True,
                linear_calibration_status=diagnostic['linear_calibration']['status'],
                confidence_calibrated=False)


def calculate(spec, recipe, *, material, train_and_forecast, kernel_factory,
              reserve, reserve_construction, save, truth, check_continue,
              training_error_factory, physical_diagnostic,
              receiver_diagnostic):
    """Keep both uncertainty targets and the whole forecast before later truth.

    The scorer reports per-axis marginal coverage for a *supplied* error law.
    Bounded/nonlinear calibration and law-estimation uncertainty remain open.
    """
    import numpy as np
    from lll.airquantumgrav_withheld_receiver import generate_full_report
    from lll.generated_prediction import calculate as physical_calculate
    if (not callable(physical_diagnostic) or not callable(receiver_diagnostic)
            or not callable(truth) or not callable(save)
            or training_error_factory is None):
        raise ValueError('both fixed-law diagnostics and training factory required')
    saved = {}
    withheld = {}

    def recorded_save(name, value):
        saved[name] = value
        save(name, value)

    def combined_diagnostic(*args, **kwargs):
        if 'forecast.json' not in saved:
            raise ValueError('saved forecast required before uncertainty diagnostics')
        physical = physical_diagnostic(*args, **kwargs)
        receiver = receiver_diagnostic(*args, **kwargs)
        if (not isinstance(physical, dict) or not isinstance(receiver, dict) or
                physical.get('prediction_target') != 'physical_position' or
                receiver.get('prediction_target') != 'receiver_measurement' or
                physical.get('later_observations_used') is not False or
                receiver.get('later_observations_used') is not False):
            raise ValueError('two earlier-only uncertainty targets required')
        recorded_save('receiver-error-diagnostic.json',json.loads(json.dumps(
            receiver, default=lambda value:value.tolist(), allow_nan=False)))
        withheld['receiver_diagnostic'] = receiver
        withheld['physical_diagnostic'] = physical
        return physical

    def later_truth(times):
        if (not {'forecast.json', 'forecast-error-diagnostic.json',
                 'receiver-error-diagnostic.json'} <= saved.keys()):
            raise ValueError('saved forecast and both uncertainty targets required before later truth')
        answer = truth(times)
        withheld['physical_truth'] = answer
        return answer

    result = physical_calculate(
        spec, recipe, material=material,
        train_and_forecast=train_and_forecast, kernel_factory=kernel_factory,
        reserve=reserve, reserve_construction=reserve_construction,
        save=recorded_save, truth=later_truth, check_continue=check_continue,
        training_error_factory=training_error_factory,
        forecast_error_diagnostic=combined_diagnostic)
    if not {'receiver_diagnostic','physical_diagnostic','physical_truth'} <= withheld.keys():
        raise ValueError('both diagnostics and withheld physical truth required')
    times = np.asarray(material['times'],dtype=float)
    cut = material['training_epochs']
    answer = withheld['physical_truth']
    receiver = generate_full_report(
        answer['coordinates'], times, material['training_rows'],
        policy_id=spec['policy_id'], seed=recipe['noise']['seed'],
        reserve=reserve_construction)
    recorded_save('later-receiver-report.json',dict(rows=receiver['rows'],
        coordinate_errors=receiver['coordinate_errors'].tolist(),
        training_prefix_exact=True,later_observations_used_for_training=False))
    receiver_coordinates = np.array([[np.radians(row['latitude_deg']),
        np.radians(row['longitude_deg']),row['height_m']] for row in receiver['rows']])
    scores = dict(physical_position=_marginal_score(
                      withheld['physical_diagnostic'],answer['coordinates'],cut),
                  receiver_measurement=_marginal_score(
                      withheld['receiver_diagnostic'],receiver_coordinates,cut),
                  training_receiver_prefix_exact=True,
                  later_observations_used_for_training=False,
                  forecast_and_diagnostics_saved_before_later_truth=True,
                  confidence_calibrated=False,scientific_decision='abstain')
    recorded_save('dual-target-scores.json',scores)
    return dict(result,dual_target=scores)
