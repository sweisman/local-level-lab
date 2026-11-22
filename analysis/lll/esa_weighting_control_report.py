# SPDX-License-Identifier: AGPL-3.0-or-later
"""Score one sealed receiver-only ESA forecast against two sealed comparators."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path


STUDY = 'data/esa-weighting-control-development-v1-20261114'
CURRENT = 'data/esa-rate-refit-development-v2-20261114'
HISTORICAL = 'docs/esa-observed-wide-pilot'
TASK = 'linear-points-receiver-only'
CURRENT_TASK = 'linear_points-increment'
HISTORICAL_TASK = 'sphere_rotating-0-reported-short-v1-0'


def score(route, receiver, *, training_epochs):
    import numpy as np
    from .airquantumgrav_geographic_report import error_metrics
    from .airquantumgrav_scoring import receiver_errors

    route = np.asarray(route, dtype=float)
    receiver = np.asarray(receiver, dtype=float)
    if (route.ndim != 2 or route.shape != receiver.shape or
            route.shape[1:] != (3,) or not np.all(np.isfinite(route)) or
            not np.all(np.isfinite(receiver)) or
            type(training_epochs) is not int or
            not 1 < training_epochs < len(route)):
        raise ValueError('matching complete three-axis routes and split required')
    errors = receiver_errors(route, receiver)
    result = {}
    for name, section in (('training', errors[:training_epochs]),
                          ('prediction', errors[training_epochs:])):
        metrics = error_metrics(section.tolist())
        metrics['maximum_horizontal_m'] = float(np.max(
            np.linalg.norm(section[:, :2], axis=1)))
        metrics['maximum_absolute_up_m'] = float(np.max(np.abs(section[:, 2])))
        result[name] = metrics
    return result


def build(root):
    import numpy as np
    from .esa_weighting_control_study import INPUT_KEYS
    from .ilvis0_prediction_observed import accuracy_screen
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    studies = [ClosedStudy(root, STUDY)]
    try:
        studies.extend([ClosedStudy(root, CURRENT), ClosedStudy(root, HISTORICAL)])
        control, current, historical = studies
        if (control.completion['state'] not in ('complete', 'terminal') or
                control.summary['completed'] != 1 or
                control.summary['total'] != 1 or
                set(control.manifest['inputs']) != set(INPUT_KEYS) or
                current.completion['manifest_sha256'] !=
                'fabb0ef004ce452a7a0b0a14ac71c307b350d3b9b4d25ca8bc8545598f75c2ba' or
                historical.completion['manifest_sha256'] !=
                '73aa91117d60ca191f614f0fe826167e8b237fcff320b7676e2f505fd1bf6289'):
            raise ValueError('exact closed comparison studies required')
        parent = control.input('parent-identity')
        if (parent != dict(prefix=CURRENT,
                           manifest_sha256=current.completion['manifest_sha256'],
                           summary_sha256=current.completion['summary_sha256'],
                           comparator=CURRENT_TASK)):
            raise ValueError('wrong sealed development parent')
        if (control.manifest['inputs']['interval']['sha256'] !=
                current.manifest['inputs']['interval']['sha256'] or
                current.manifest['inputs']['interval']['sha256'] !=
                historical.manifest['inputs']['interval']['sha256'] or
                control.manifest['inputs']['training']['sha256'] !=
                current.manifest['inputs']['training']['sha256'] or
                current.manifest['inputs']['training']['sha256'] !=
                historical.manifest['inputs']['training']['sha256'] or
                current.manifest['inputs']['training']['sha256'] !=
                'd37af49e9b8a718ff3cca60ebd47cd0f82fef6a6ec466e197eae10d027f437d1'):
            raise ValueError('original intervals or training rows differ')
        selected = ((control, TASK), (current, CURRENT_TASK),
                    (historical, HISTORICAL_TASK))
        routes = {}
        records = {}
        training = []
        for sealed, identity in selected:
            envelope = sealed.envelope(identity)
            fit = sealed.artifact(identity, 'fit.json')
            forecast = sealed.artifact(identity, 'forecast.json')
            observations = sealed.artifact(identity, 'training-observations.json')
            if (fit['model'] != 'sphere_rotating' or
                    fit['active_parameters'] != forecast['active_parameters'] or
                    forecast['training_epochs'] != 800 or
                    forecast['prediction_epochs'] != 400 or
                    len(forecast['coordinates']) != 1200 or
                    forecast['prediction_receiver_positions_used'] is not False or
                    envelope['result'].get('scientific_decision') != 'abstain'):
                raise ValueError('matched sealed training-only forecast required')
            training.append({key: observations[key] for key in
                ('training_epochs', 'prediction_epochs', 'native_prefix_packets',
                 'weight_configuration', 'time_origin_gps_sow_s',
                 'training_prefix_sha256')})
            routes[identity] = forecast
            records[identity] = dict(converged=fit['converged'],
                evaluations=fit['evaluations'],
                normalized_parameters=fit['normalized_parameters'],
                active_parameters=fit['active_parameters'],
                active_bounds=fit['active_bounds'],
                residual_sum_squares=fit['residual_sum_squares'])
        if training[0] != training[1] or training[1] != training[2]:
            raise ValueError('same receiver weighting and IMU prefix required')
        if not (routes[TASK]['times_s'] == routes[CURRENT_TASK]['times_s'] ==
                routes[HISTORICAL_TASK]['times_s']):
            raise ValueError('different later query support')
        exact_historical_reproduction = (
            routes[TASK]['coordinates'] == routes[HISTORICAL_TASK]['coordinates']
            and records[TASK]['normalized_parameters'] ==
                records[HISTORICAL_TASK]['normalized_parameters'])
        if not exact_historical_reproduction:
            raise ValueError('receiver-only fit does not reproduce historical forecast')
        # All three training-only forecasts are sealed before opening scoring.
        rows = json.loads(gzip.decompress(historical.input('scoring', raw=True)))
        if (len(rows) != 1200 or historical.manifest['inputs']['scoring']['sha256'] !=
                '5cce2704433e7dece8eec336882692e15194d6c882d8e2bd7efa67265a172c2b'):
            raise ValueError('unchanged complete later receiver rows required')
        receiver = np.asarray([[math.radians(row['latitude_deg']),
                                math.radians(row['longitude_deg']),
                                row['height_m']] for row in rows])
        for identity in routes:
            section = score(routes[identity]['coordinates'], receiver,
                            training_epochs=800)
            records[identity].update(section)
            records[identity]['physical_accuracy'] = {name:
                accuracy_screen(section[name]) for name in ('training', 'prediction')}
        if (abs(records[HISTORICAL_TASK]['prediction']['horizontal_rms_m']-
                7.802722559272892) > 1e-6 or
                abs(records[CURRENT_TASK]['prediction']['horizontal_rms_m']-
                    249.41078308821852) > 1e-6):
            raise ValueError('saved reference scoring changed')
        active = records[TASK]['active_parameters']
        if (active != records[CURRENT_TASK]['active_parameters'] or active !=
                records[HISTORICAL_TASK]['active_parameters']):
            raise ValueError('calibration columns changed')
        index = active.index('gyro_bias_z')
        result = dict(study=STUDY,
            control_manifest_sha256=control.completion['manifest_sha256'],
            control_summary_sha256=control.completion['summary_sha256'],
            current_manifest_sha256=current.completion['manifest_sha256'],
            historical_manifest_sha256=historical.completion['manifest_sha256'],
            scoring_sha256=historical.manifest['inputs']['scoring']['sha256'],
            exact_historical_reproduction=exact_historical_reproduction,
            report_source_sha256=hashlib.sha256((root/
                'analysis/lll/esa_weighting_control_report.py').read_bytes()).hexdigest(),
            training_epochs=800, prediction_epochs=400,
            training_binding=training[0], cases=records,
            gyro_bias_z_normalized={identity: records[identity][
                'normalized_parameters'][index] for identity in records},
            confidence_calibrated=False, scientific_decision='abstain')
        return result
    finally:
        for study in reversed(studies):
            study.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    result = build(args.root)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps({key: dict(converged=value['converged'],
        training_horizontal_rms_m=value['training']['horizontal_rms_m'],
        later_horizontal_rms_m=value['prediction']['horizontal_rms_m'])
        for key, value in result['cases'].items()}, sort_keys=True))


if __name__ == '__main__':
    main()
