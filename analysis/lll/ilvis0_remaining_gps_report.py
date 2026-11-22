# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify the twenty-group GPS forecast and summarize matched outcomes."""

from collections import Counter
from contextlib import closing
from pathlib import Path
from statistics import median

from .ilvis0_remaining_gps_baseline import ID, ORIGINS
from .receiver_only_forecast_report import replay
from .studies.closed import ClosedStudy


RESULT = 'docs/prediction-group-transfer/remaining-gps-baseline.json'
METRICS = ('horizontal_rms_m', 'vertical_rms_m')


def physical(scores):
    return (scores['horizontal_rms_m'] <= 10. and scores['vertical_rms_m'] <= 30.
            and scores['maximum_horizontal_m'] <= 50. and scores['maximum_absolute_up_m'] <= 150.)


def comparisons(rows):
    output = []
    for origin in ORIGINS:
        values = [v for v in rows if v['origin'] == origin]
        matched = [v for v in values if v['imu'] is not None]
        metrics = {}
        for name in METRICS:
            gps = [v['gps'][name] for v in matched]
            imu = [v['imu']['scores'][name] for v in matched]
            if not gps:
                continue
            metrics[name] = dict(gps_all_median=median(v['gps'][name] for v in values),
                gps_matched_median=median(gps), imu_matched_median=median(imu),
                gps_lower=sum(a < b for a, b in zip(gps, imu, strict=True)),
                imu_lower=sum(b < a for a, b in zip(gps, imu, strict=True)))
        output.append(dict(origin=origin, groups=len(values), matched=len(matched),
            gps_physical=sum(physical(v['gps']) for v in values),
            gps_matched_physical=sum(physical(v['gps']) for v in matched),
            imu_matched_physical=sum(physical(v['imu']['scores']) for v in matched), metrics=metrics))
    return output


def collect(root):
    rows = []
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if not study.summary['passed'] or study.summary['completed'] != 40 or study.summary['bound_evaluations'] != 40:
            raise ValueError('all forty charged GPS-only forecasts must complete')
        for identity in study.tasks:
            row = study.envelope(identity)['result']
            training = study.input(identity+'-training')
            scoring = study.input(identity+'-scoring')
            forecast = study.artifact(identity, 'forecast.json')
            epochs = study.artifact(identity, 'epochs.json')
            if (row['imu_samples_used'] != 0 or row['scientific_decision'] != 'abstain'
                    or forecast['later_positions_used'] or row['imu'] != scoring['imu']
                    or forecast['times'] != training['future_times']
                    or [v['time_s'] for v in epochs] != forecast['times']
                    or len(forecast['coordinates']) != row['horizon'] or replay(epochs) != row['gps']):
                raise ValueError('sealed training, prediction and scoring records must agree')
            score = dict(row['gps'])
            score['vertical_rms_m'] = score.pop('up_rms_m')
            rows.append(dict(row, gps=score))
        groups = Counter((v['group_id'], v['origin']) for v in rows)
        if len(groups) != 40 or len({group for group, _ in groups}) != 20:
            raise ValueError('twenty conservative groups must appear once at each cut')
        return dict(rows=rows, comparisons=comparisons(rows), manifest_sha256=study.completion['manifest_sha256'],
                    new_fits=0, scientific_decision='abstain')


if __name__ == '__main__':
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.artifacts import digest, encoded

    root = Path.cwd()
    raw = encoded(collect(root))
    _write_equal(root/RESULT, raw)
    print(digest(raw))
