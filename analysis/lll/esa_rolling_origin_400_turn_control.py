# SPDX-License-Identifier: AGPL-3.0-or-later
"""Score a later-designed GPS-only constant-turn control on one ESA window."""

import gzip
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from .esa_rolling_origin_400_score import PARENT, score_raw
from .esa_rolling_origin_400_study import ID as FIT_ID
from .receiver_only_constant_turn import forecast_constant_turn


def build(root):
    from .esa_rolling_origin_400_velocity_control import build as velocity_control
    from .studies.artifacts import encoded
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    previous = velocity_control(root)
    fit = ClosedStudy(root, 'data/' + FIT_ID)
    parent = ClosedStudy(root, PARENT)
    try:
        if (previous['fit_manifest_sha256'] != fit.completion['manifest_sha256'] or
                previous['parent_manifest_sha256'] != parent.completion['manifest_sha256']):
            raise ValueError('sealed development identities differ')
        rows = json.loads(gzip.decompress(parent.input('training', raw=True)))
        forecast = fit.artifact('increment', 'forecast.json')
        times = np.asarray(forecast['times_s'], dtype=float)
        if len(rows) != 800 or len(times) != 520:
            raise ValueError('same complete 400/120 receiver cut required')
        offset = rows[0]['time_s']-times[0]
        earlier = np.asarray([row['time_s']-offset for row in rows[340:400]])
        if not np.allclose(earlier, times[340:400], atol=1e-6, rtol=0):
            raise ValueError('last 60 earlier receiver times differ')
        velocity = np.asarray([[r['north_mps'], r['east_mps'], r['up_mps']]
                               for r in rows[340:400]], dtype=float)

        def coordinate(row):
            return [math.radians(row['latitude_deg']),
                    math.radians(row['longitude_deg']), row['height_m']]

        predicted = forecast_constant_turn(
            earlier, velocity, coordinate(rows[399]), times[400:520])
        observed = np.asarray([coordinate(r) for r in rows[400:520]], dtype=float)
        score = score_raw(predicted['coordinates'], observed)
        return dict(version='esa-rolling-origin-400-turn-control-v1',
                    designed_after_fixed_course_results=True,
                    previous_control_sha256=hashlib.sha256(encoded(previous)).hexdigest(),
                    fit_manifest_sha256=fit.completion['manifest_sha256'],
                    parent_manifest_sha256=parent.completion['manifest_sha256'],
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    rule_sha256=hashlib.sha256((root /
                        'analysis/lll/receiver_only_constant_turn.py').read_bytes()).hexdigest(),
                    earlier_receiver_reports=400, later_receiver_reports=120,
                    training_course_reports=60,
                    fitted_course_turn_deg_per_min=math.degrees(
                        predicted['course_rate_rads'])*60,
                    final_training_speed_mps=predicted['final_training_speed_mps'],
                    final_training_up_mps=predicted['final_training_up_mps'],
                    no_imu_samples=predicted['imu_samples_used'] == 0,
                    later_positions_used_for_forecast=predicted['later_positions_used'],
                    constant_turn_score=score,
                    fixed_velocity_score=previous['reported_velocity_control']['score'],
                    sealed_imu=previous['sealed_imu'],
                    original_reads=0, protected_reads=0, new_model_fits=0,
                    independent_validation=False, calibrated_coverage=False,
                    gyro_contribution_isolated=False,
                    scientific_decision='abstain')
    finally:
        parent.close()
        fit.close()


def publish(root):
    from .studies.artifacts import atomic, encoded

    root = Path(root).resolve()
    result = build(root)
    base = root / 'docs/prediction-observed-development'
    atomic(base / 'ROLLING_ORIGIN_400_TURN_CONTROL.json', encoded(result))
    turn = result['constant_turn_score']['metrics']
    fixed = result['fixed_velocity_score']['metrics']
    imu = result['sealed_imu']['increment']
    page = ('# GPS-only constant-turn forecast\n\n'
        'This development rule was designed after the fixed-course GPS-only '
        'controls were scored. It fits one course turn rate to the last 60 '
        'earlier GNSS velocity reports and forecasts the same later 120 times. '
        'It uses no IMU data or later GNSS value to make its forecast.\n\n'
        f"The earlier fitted course turn rate is {result['fitted_course_turn_deg_per_min']:.3f} "
        'degrees per minute.\n\n'
        '| Forecast | Later horizontal RMS (m) | Later height RMS (m) |\n'
        '| --- | ---: | ---: |\n'
        f'| GPS-only, constant turn | {turn["horizontal_rms_m"]:.3f} | '
        f'{turn["vertical_rms_m"]:.3f} |\n'
        f'| GPS-only, fixed reported velocity | {fixed["horizontal_rms_m"]:.3f} | '
        f'{fixed["vertical_rms_m"]:.3f} |\n'
        f'| Sealed conditioned IMU | {imu["conditioned_horizontal_rms_m"]:.3f} | '
        f'{imu["conditioned_vertical_rms_m"]:.3f} |\n\n'
        'This single previously opened window is exploratory. The two GNSS '
        'fields share one PPP solution; the forecast is not an independent '
        'motion standard. Neither its success nor its failure isolates the '
        'gyroscope contribution or calibrates prediction coverage. No '
        'Earth-model decision follows.\n\n'
        '[Fixed method](ROLLING_ORIGIN_400_TURN_CONTROL_PLAN.md) · '
        '[Detailed result](ROLLING_ORIGIN_400_TURN_CONTROL.json).\n')
    atomic(base / 'ROLLING_ORIGIN_400_TURN_CONTROL.md', page.encode())
    return result


if __name__ == '__main__':
    outcome = publish('.')
    print(json.dumps(outcome['constant_turn_score']['metrics'], sort_keys=True))
