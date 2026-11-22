# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare fixed receiver-only rules on the sealed ESA 400/120 window."""

import gzip
import hashlib
import json
import math
from pathlib import Path

from .esa_rolling_origin_400_score import PARENT
from .esa_rolling_origin_400_study import ID as FIT_ID, LAWS


def score_receiver_only(times_s, receiver_coordinates):
    """Score two unchanged earlier-only rules on exactly 400 + 120 reports."""
    import numpy as np
    from .prediction_observed_drift_report import receiver_reference

    times = np.asarray(times_s, dtype=float)
    coordinates = np.asarray(receiver_coordinates, dtype=float)
    if times.shape != (520,) or coordinates.shape != (520, 3):
        raise ValueError('exactly 520 aligned receiver times and coordinates required')
    return receiver_reference(times, coordinates, 400)


def build(root):
    import numpy as np
    from .esa_rolling_origin_400_conditioning_score import build as conditional_score
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    prior = conditional_score(root)
    fit = ClosedStudy(root, 'data/' + FIT_ID)
    parent = ClosedStudy(root, PARENT)
    try:
        if (prior['fit_manifest_sha256'] != fit.completion['manifest_sha256'] or
                prior['parent_manifest_sha256'] != parent.completion['manifest_sha256'] or
                prior['training_receiver_reports'] != 400 or
                prior['withheld_receiver_reports'] != 120):
            raise ValueError('sealed study identities or split differ')
        rows = json.loads(gzip.decompress(parent.input('training', raw=True)))
        if len(rows) != 800:
            raise ValueError('complete receiver source required')
        forecasts = [fit.artifact(law, 'forecast.json') for law in LAWS]
        times = np.asarray(forecasts[0]['times_s'], dtype=float)
        if (len(times) != 520 or
                any(f['times_s'] != forecasts[0]['times_s'] for f in forecasts) or
                any(f['training_epochs'] != 400 or f['prediction_epochs'] != 120 or
                    f['prediction_receiver_positions_used'] is not False
                    for f in forecasts)):
            raise ValueError('sealed forecasts do not share the exact 400/120 cut')
        receiver_times = np.asarray([float(r['time_s']) for r in rows[:520]])
        if (not np.all(np.diff(times) > 0) or
                not np.all(np.diff(receiver_times) > 0) or
                np.max(np.abs((receiver_times - times) -
                              (receiver_times[0] - times[0]))) > 1e-6):
            raise ValueError('forecast times do not align with receiver times')
        coordinates = np.asarray([[math.radians(r['latitude_deg']),
            math.radians(r['longitude_deg']), r['height_m']]
            for r in rows[:520]], dtype=float)
        control = score_receiver_only(times, coordinates)
        comparison = {law: {
            'raw_horizontal_rms_m': prior['laws'][law]['score']['raw']['metrics']['horizontal_rms_m'],
            'conditioned_horizontal_rms_m': prior['laws'][law]['score']['conditional']['metrics']['horizontal_rms_m'],
            'conditioned_vertical_rms_m': prior['laws'][law]['score']['conditional']['metrics']['vertical_rms_m'],
        } for law in LAWS}
        return dict(version='esa-rolling-origin-400-receiver-control-v1',
            fit_manifest_sha256=fit.completion['manifest_sha256'],
            fit_summary_sha256=fit.completion['summary_sha256'],
            parent_manifest_sha256=parent.completion['manifest_sha256'],
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            receiver_rule_sha256={name: hashlib.sha256((root / 'analysis/lll' /
                (name + '.py')).read_bytes()).hexdigest() for name in
                ('receiver_only_forecast', 'receiver_only_geodesic')},
            training_receiver_reports=400, withheld_receiver_reports=120,
            receiver_only=control, sealed_imu=comparison,
            original_reads=0, protected_reads=0, new_model_fits=0,
            independent_validation=False, calibrated_coverage=False,
            scientific_decision='abstain')
    finally:
        parent.close()
        fit.close()


def publish(root):
    from .studies.artifacts import atomic, encoded

    root = Path(root).resolve()
    result = build(root)
    base = root / 'docs/prediction-observed-development'
    atomic(base / 'ROLLING_ORIGIN_400_RECEIVER_CONTROL.json', encoded(result))
    rows = []
    for name in ('linear', 'geodesic'):
        item = result['receiver_only'][name]
        rows.append(f'| Receiver only: {name} | {item["horizontal_rms_m"]:.3f} | '
                    f'{item["vertical_rms_m"]:.3f} |')
    for name in LAWS:
        item = result['sealed_imu'][name]
        rows.append(f'| IMU plus receiver: {name}, conditioned | '
                    f'{item["conditioned_horizontal_rms_m"]:.3f} | '
                    f'{item["conditioned_vertical_rms_m"]:.3f} |')
    page = ('# Receiver-only forecast control\n\n'
        'On the same preselected 400-training/120-later ESA development window, '
        'two fixed rules predict from earlier GPS receiver positions alone. '
        'Neither uses IMU data or later receiver positions to make its forecast. '
        'The IMU rows reuse the sealed early-only conditioned forecasts.\n\n'
        '| Forecast | Later horizontal RMS (m) | Later height RMS (m) |\n'
        '| --- | ---: | ---: |\n' + '\n'.join(rows) + '\n\n'
        'The receiver-only rules estimate speed from the last minute of '
        'positions and hold it constant. They do not use the receiver export’s '
        'reported velocity columns or adapt to later turns. '
        'Their large miss on this maneuvering window does not prove that the '
        'gyro alone caused the IMU forecast advantage: accelerometers, model '
        'assumptions and the earlier receiver correction contribute too. '
        'This is one development recording, not independent validation or a '
        'calibrated physical-accuracy claim. No Earth-model decision follows.\n\n'
        '[Fixed rules and selection](ROLLING_ORIGIN_400_RECEIVER_CONTROL_PLAN.md) · '
        '[Detailed result](ROLLING_ORIGIN_400_RECEIVER_CONTROL.json).\n')
    atomic(base / 'ROLLING_ORIGIN_400_RECEIVER_CONTROL.md', page.encode())
    return result


if __name__ == '__main__':
    print(json.dumps({name: row['horizontal_rms_m'] for name, row in
                      publish('.')['receiver_only'].items()}, sort_keys=True))
