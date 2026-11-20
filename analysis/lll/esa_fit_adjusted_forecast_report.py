# SPDX-License-Identifier: AGPL-3.0-or-later
"""Score sealed generated ESA forecasts against unused analytic future truth."""

import argparse
import hashlib
import json
import math
from pathlib import Path


TRUTH_SOURCES = (
    'analysis/lll/airquantumgrav_truth.py',
    'analysis/lll/airquantumgrav_observation_truth.py',
)


def ecef_coordinates(coordinates):
    """Forward ellipsoidal conversion, independent of forecast propagation."""
    import numpy as np
    from .airquantumgrav_truth import A, E2

    values = np.asarray(coordinates, dtype=float)
    if (values.ndim != 2 or values.shape[1:] != (3,) or not len(values)
            or not np.all(np.isfinite(values)) or
            np.any(abs(values[:, 0]) >= math.pi/2)):
        raise ValueError('finite nonpolar coordinate triples required')
    phi, longitude, height = values.T
    radius = A/np.sqrt(1-E2*np.sin(phi)**2)
    horizontal = (radius+height)*np.cos(phi)
    return np.column_stack((horizontal*np.cos(longitude),
        horizontal*np.sin(longitude),
        (radius*(1-E2)+height)*np.sin(phi)))


def position_errors_neu(predicted, true_coordinates):
    """Exact ECEF difference projected at each true ellipsoidal coordinate."""
    import numpy as np

    predicted = np.asarray(predicted, dtype=float)
    true_coordinates = np.asarray(true_coordinates, dtype=float)
    if predicted.shape != true_coordinates.shape:
        raise ValueError('aligned finite nonpolar coordinates required')
    delta = ecef_coordinates(predicted)-ecef_coordinates(true_coordinates)
    phi, longitude = true_coordinates[:, 0], true_coordinates[:, 1]
    north = (-np.sin(phi)*np.cos(longitude)*delta[:, 0]
             -np.sin(phi)*np.sin(longitude)*delta[:, 1]
             +np.cos(phi)*delta[:, 2])
    east = -np.sin(longitude)*delta[:, 0]+np.cos(longitude)*delta[:, 1]
    up = (np.cos(phi)*np.cos(longitude)*delta[:, 0]
          +np.cos(phi)*np.sin(longitude)*delta[:, 1]
          +np.sin(phi)*delta[:, 2])
    return np.column_stack((north, east, up))


def _metrics(errors):
    import numpy as np

    errors = np.asarray(errors, dtype=float)
    rms = np.sqrt(np.mean(errors*errors, axis=0))
    return dict(rms_neu_m=rms.tolist(),
        horizontal_rms_m=float(np.linalg.norm(rms[:2])),
        vertical_rms_m=float(rms[2]),
        maximum_3d_m=float(np.max(np.linalg.norm(errors, axis=1))),
        signed_mean_neu_m=np.mean(errors, axis=0).tolist())


def calibration_truth_distance(fit, truth, limits):
    """Compare only directly generated sensor calibration coordinates."""
    names = tuple(name for name in fit['active_parameters']
        if name.startswith(('gyro_bias_', 'accel_bias_',
                            'gyro_gain_', 'accel_gain_')) or name == 'time_offset')
    point = dict(zip(fit['active_parameters'],
                     fit['normalized_parameters'], strict=True))
    if (len(names) != 13 or any(name not in truth or name not in limits or
            limits[name] <= 0 or not math.isfinite(point[name])
            for name in names)):
        raise ValueError('complete directly generated sensor calibration required')
    rows = {name:dict(truth_normalized=float(truth[name]/limits[name]),
                      fitted_normalized=float(point[name]),
                      absolute_difference_normalized=float(abs(
                          point[name]-truth[name]/limits[name])))
            for name in names}
    return dict(parameters=rows,
        maximum_absolute_difference_normalized=max(
            item['absolute_difference_normalized'] for item in rows.values()))


def build(root):
    import numpy as np
    from .esa_fit_adjusted_control_report import build as control_build, _study
    from .esa_fit_adjusted_control_study import LAWS
    from .airquantumgrav_observation_truth import receiver_samples, sensor_parameters

    root = Path(root).resolve()
    control = control_build(root)
    study, lineage = _study(root)
    try:
        if (lineage != control['continuation_lineage_sha256'] or
                set(control['cases']) != set(LAWS) or
                any(study.manifest['sources'].get(source) !=
                    hashlib.sha256((root/source).read_bytes()).hexdigest()
                    for source in TRUTH_SOURCES)):
            raise ValueError('frozen generated truth source differs')
        cases = {}
        calibration_truth = sensor_parameters(1)
        calibration_limits = study.input('recipe')['limits']
        for truth_law in LAWS:
            payload = study.tasks[truth_law]['payload']
            if (payload['model'] != 'sphere_rotating' or
                    payload['truth_law'] != truth_law or
                    payload['latitude_deg'] != 55. or
                    payload['start'] != 0 or payload['profile'] is not False):
                raise ValueError('unchanged known-answer task required')
            times = .5+np.arange(900.)
            answer = receiver_samples('sphere_rotating', times[600:],
                latitude_deg=payload['latitude_deg'], pattern='fast',
                removal=0., sign=1, height_profile='climb',
                gravity_model='inverse_square_height')
            true = answer['coordinates']
            truth_reconstruction_error = float(np.max(np.linalg.norm(
                ecef_coordinates(true)-answer['position_world_m'], axis=1)))
            if truth_reconstruction_error > 1e-5:
                raise ValueError('independent truth-coordinate reconstruction differs')
            candidates = {}
            for law in LAWS:
                forecast = study.artifact(truth_law, law+'/forecast.json')
                fit = study.artifact(truth_law, law+'/fit.json')
                if (forecast['training_epochs'] != 600 or
                        forecast['prediction_epochs'] != 300 or
                        forecast['prediction_receiver_positions_used'] is not False or
                        forecast['continuous_propagation_without_gps_reset'] is not True or
                        forecast['frozen_error_model'] != 'sphere_rotating' or
                        forecast['times_s'] != times.tolist() or
                        fit['converged'] is not True or
                        fit['stopping_rule_verified'] is not True or
                        control['cases'][truth_law]['candidates'][law]['status']
                            != 'bound_active'):
                    raise ValueError('sealed matched forecast or fit differs')
                predicted = np.asarray(forecast['coordinates'], dtype=float)
                if predicted.shape != (900, 3):
                    raise ValueError('complete saved forecast coordinates required')
                errors = position_errors_neu(predicted[600:], true)
                candidates[law] = dict(
                    full_future=_metrics(errors),
                    hundred_report_bins=[_metrics(errors[i:i+100])
                        for i in (0, 100, 200)],
                    directly_generated_calibration=calibration_truth_distance(
                        fit, calibration_truth, calibration_limits),
                    later_truth_used_to_fit=False,
                    physical_accuracy_calibrated=False)
            cases[truth_law] = dict(candidates=candidates,
                truth_ecef_reconstruction_max_m=truth_reconstruction_error)
        return dict(version='esa-fit-adjusted-forecast-report-v1',
            study=control['study'],
            study_manifest_sha256=control['study_manifest_sha256'],
            study_summary_sha256=control['study_summary_sha256'],
            report_source_sha256=hashlib.sha256((root/
                'analysis/lll/esa_fit_adjusted_forecast_report.py').read_bytes()
                ).hexdigest(),
            truth_source_sha256={source:study.manifest['sources'][source]
                for source in TRUTH_SOURCES},
            cases=cases,generated_recordings=2,attempted_fits=4,
            original_reads=0,protected_confirmation_groups_opened=0,
            native_calls=0,nonlinear_refit_performed=False,
            receiver_noise_added_to_future_truth=False,
            error_law_qualified=False,scientific_decision='abstain')
    finally:
        study.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    result = build(args.root)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps({truth:{law:row['full_future']
        for law,row in case['candidates'].items()} for truth,case in
        result['cases'].items()},sort_keys=True))


if __name__ == '__main__':
    main()
