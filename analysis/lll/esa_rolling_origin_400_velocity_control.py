# SPDX-License-Identifier: AGPL-3.0-or-later
"""Score a later-designed GNSS-velocity control on the opened ESA window."""

import gzip
import hashlib
import json
import math
from pathlib import Path

from .esa_rolling_origin_400_score import PARENT, score_raw
from .esa_rolling_origin_400_study import ID as FIT_ID


def score_velocity(last_time, last_coordinate, last_velocity,
                   future_times, future_receiver):
    from .receiver_only_velocity import forecast_velocity

    forecast = forecast_velocity(last_time, last_coordinate,
                                 last_velocity, future_times)
    return dict(forecast=dict(
        north_east_up_velocity_mps=forecast['north_east_up_velocity_mps'].tolist(),
        last_training_time_s=forecast['last_training_time_s'],
        imu_samples_used=forecast['imu_samples_used'],
        later_positions_used=forecast['later_positions_used']),
        score=score_raw(forecast['coordinates'], future_receiver))


def build(root):
    import numpy as np
    from .esa_rolling_origin_400_receiver_control import build as first_control
    from .studies.artifacts import encoded
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    first = first_control(root)
    fit = ClosedStudy(root, 'data/' + FIT_ID)
    parent = ClosedStudy(root, PARENT)
    try:
        if (first['fit_manifest_sha256'] != fit.completion['manifest_sha256'] or
                first['parent_manifest_sha256'] != parent.completion['manifest_sha256']):
            raise ValueError('earlier receiver control and sealed inputs differ')
        rows = json.loads(gzip.decompress(parent.input('training', raw=True)))
        forecast = fit.artifact('increment', 'forecast.json')
        times = np.asarray(forecast['times_s'], dtype=float)
        if len(rows) != 800 or len(times) != 520:
            raise ValueError('same complete 400/120 receiver cut required')
        offset = rows[0]['time_s'] - times[0]
        if any(abs(rows[i]['time_s'] - times[i] - offset) > 1e-6
               for i in range(520)):
            raise ValueError('forecast and receiver times differ')
        def coordinate(row):
            return [math.radians(row['latitude_deg']),
                    math.radians(row['longitude_deg']), row['height_m']]
        last = rows[399]
        later = np.asarray([coordinate(row) for row in rows[400:520]], float)
        velocity = [last['north_mps'], last['east_mps'], last['up_mps']]
        control = score_velocity(times[399], coordinate(last), velocity,
                                 times[400:], later)
        return dict(version='esa-rolling-origin-400-velocity-control-v1',
            designed_after_first_receiver_control=True,
            first_control_sha256=hashlib.sha256(encoded(first)).hexdigest(),
            fit_manifest_sha256=fit.completion['manifest_sha256'],
            parent_manifest_sha256=parent.completion['manifest_sha256'],
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            velocity_rule_sha256=hashlib.sha256((root /
                'analysis/lll/receiver_only_velocity.py').read_bytes()).hexdigest(),
            training_receiver_reports=400, withheld_receiver_reports=120,
            last_earlier_report_index=399,
            reported_velocity_control=control,
            earlier_fixed_receiver_rules={name: {
                'horizontal_rms_m': row['horizontal_rms_m'],
                'vertical_rms_m': row['vertical_rms_m']}
                for name, row in first['receiver_only'].items()},
            sealed_imu=first['sealed_imu'], original_reads=0,
            protected_reads=0, new_model_fits=0,
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
    atomic(base / 'ROLLING_ORIGIN_400_VELOCITY_CONTROL.json', encoded(result))
    new = result['reported_velocity_control']['score']['metrics']
    old = result['earlier_fixed_receiver_rules']
    imu = result['sealed_imu']['increment']
    page = ('# Reported-velocity receiver control\n\n'
        'This follow-up was designed **after** seeing that two position-only '
        'receiver rules missed the ESA development window. It uses the last '
        'earlier GNSS-reported velocity, keeps it constant and predicts the '
        'same later 120 times. It does not use IMU samples or later receiver '
        'values to make its forecast.\n\n'
        '| Forecast | Later horizontal RMS (m) | Later height RMS (m) |\n'
        '| --- | ---: | ---: |\n'
        f'| Receiver, reported velocity | {new["horizontal_rms_m"]:.3f} | '
        f'{new["vertical_rms_m"]:.3f} |\n'
        f'| Receiver, position-derived linear | {old["linear"]["horizontal_rms_m"]:.3f} | '
        f'{old["linear"]["vertical_rms_m"]:.3f} |\n'
        f'| Receiver, position-derived geodesic | {old["geodesic"]["horizontal_rms_m"]:.3f} | '
        f'{old["geodesic"]["vertical_rms_m"]:.3f} |\n'
        f'| Sealed conditioned IMU forecast | {imu["conditioned_horizontal_rms_m"]:.3f} | '
        f'{imu["conditioned_vertical_rms_m"]:.3f} |\n\n'
        'These are comparisons with specific fixed forecast rules on one '
        'development recording. The reported GNSS velocity is not an '
        'independently calibrated trajectory or a future turn forecast. '
        'Neither this comparison nor the earlier one isolates the gyro '
        'channel or validates prediction coverage. No Earth-model decision '
        'follows.\n\n'
        '[Chronology and rule](ROLLING_ORIGIN_400_VELOCITY_CONTROL_PLAN.md) · '
        '[Detailed result](ROLLING_ORIGIN_400_VELOCITY_CONTROL.json).\n')
    atomic(base / 'ROLLING_ORIGIN_400_VELOCITY_CONTROL.md', page.encode())
    return result


if __name__ == '__main__':
    outcome = publish('.')
    print(json.dumps(outcome['reported_velocity_control']['score']['metrics'],
                     sort_keys=True))
