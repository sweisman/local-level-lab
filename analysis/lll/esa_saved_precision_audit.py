# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare sealed ESA forecast errors with matching receiver-reported precision."""
import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import statistics
from pathlib import Path

from lll.studies.closed import ClosedStudy


PARENT = 'docs/esa-observed-wide-pilot'
MANIFEST_SHA256 = '73aa91117d60ca191f614f0fe826167e8b237fcff320b7676e2f505fd1bf6289'
SUMMARY_SHA256 = '2ce3ae7c4e48adb8d5d3048316a68d88a3015ff1528a3515bb212d1081e15f31'
SCORING_SHA256 = '5cce2704433e7dece8eec336882692e15194d6c882d8e2bd7efa67265a172c2b'
AXES = ('north', 'east', 'height')


def summarize(scores, receiver_rows, *, training_epochs):
    """Return later-epoch descriptive values after an exact receiver join."""
    times = scores['times_s']
    coords = scores['receiver_coordinates']
    errors = scores['errors_neu_m']
    count = len(receiver_rows)
    if (count != len(times) or count != len(coords) or count != len(errors)
            or type(training_epochs) is not int or not 0 < training_epochs < count):
        raise ValueError('complete matching receiver epochs and training cut required')
    origin_receiver = receiver_rows[0]['time_s']
    origin_score = times[0]
    for index, (row, time, coordinate, error) in enumerate(zip(receiver_rows, times, coords, errors, strict=True)):
        if (not math.isfinite(time) or not math.isfinite(row['time_s'])
                or (index and (time <= times[index - 1] or row['time_s'] <= receiver_rows[index - 1]['time_s']))
                or not math.isclose(time - origin_score, row['time_s'] - origin_receiver,
                                    rel_tol=0, abs_tol=1e-9)):
            raise ValueError('receiver and forecast time mismatch')
        expected = (math.radians(row['latitude_deg']), math.radians(row['longitude_deg']), row['height_m'])
        if (len(coordinate) != 3 or any(not math.isfinite(a) or not math.isclose(a, b, rel_tol=0, abs_tol=1e-10)
                                        for a, b in zip(coordinate, expected, strict=True))):
            raise ValueError('receiver and forecast coordinate mismatch')
        variance = row['position_variance_m2']
        if (len(variance) != 3 or len(error) != 3 or any(not math.isfinite(v) or v <= 0 for v in variance)
                or any(not math.isfinite(v) for v in error)):
            raise ValueError('finite positive receiver variance and finite forecast error required')
    result = {'prediction_epochs': count - training_epochs, 'scientific_decision': 'abstain'}
    for axis, name in enumerate(AXES):
        tail = [(abs(errors[i][axis]), math.sqrt(receiver_rows[i]['position_variance_m2'][axis]))
                for i in range(training_epochs, count)]
        result[name] = {
            'error_rms_m': math.sqrt(sum(errors[i][axis] ** 2 for i in range(training_epochs, count)) / len(tail)),
            'median_receiver_sigma_m': statistics.median(sigma for _, sigma in tail),
            'median_abs_error_over_sigma': statistics.median(error / sigma for error, sigma in tail),
        }
    return result


def build(root):
    """Read only the sealed development study; preserve every task identity."""
    root = Path(root).resolve()
    study = ClosedStudy(root, PARENT)
    try:
        if (study.completion['state'] != 'terminal' or
                study.completion['manifest_sha256'] != MANIFEST_SHA256 or
                study.completion['summary_sha256'] != SUMMARY_SHA256 or
                study.manifest['inputs']['scoring']['sha256'] != SCORING_SHA256 or
                len(study.tasks) != 24 or len(study.rows) != 24 or
                sum(row['passed'] for row in study.rows.values()) != 22):
            raise ValueError('exact sealed 24-task ESA development parent required')
        receiver_rows = json.loads(gzip.decompress(study.input('scoring', raw=True)))
        if len(receiver_rows) != 1200:
            raise ValueError('1200 sealed receiver epochs required')
        result = []
        for identity in study.tasks:
            row = study.rows[identity]
            item = {'identity': identity, 'status': row['status'], 'passed': row['passed'],
                    'forecast_available': False, 'metrics': None}
            if row['passed']:
                scores = study.artifact(identity, 'scores.json')
                forecast = study.artifact(identity, 'forecast.json')
                if forecast['training_epochs'] != 800 or forecast['prediction_epochs'] != 400:
                    raise ValueError('unchanged 800/400 forecast split required')
                item['forecast_available'] = True
                item['metrics'] = summarize(scores, receiver_rows, training_epochs=800)
                if item['metrics']['prediction_epochs'] != 400:
                    raise ValueError('complete later forecast required')
            else:
                item['reason'] = study.envelope(identity)['result'].get('reason')
            result.append(item)
        source = root / 'analysis/lll/esa_saved_precision_audit.py'
        return {'parent': PARENT, 'parent_manifest_sha256': MANIFEST_SHA256,
                'parent_summary_sha256': SUMMARY_SHA256, 'scoring_sha256': SCORING_SHA256,
                'reporter_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                'tasks': result, 'total': len(result), 'forecasts': sum(v['forecast_available'] for v in result),
                'scientific_decision': 'abstain', 'native_calls': 0, 'original_reads': 0,
                'protected_reads': 0}
    finally:
        study.close()


def publish(root, output='docs/esa-prediction-error-scale'):
    report = build(root)
    target = Path(root) / output
    target.mkdir(parents=True, exist_ok=True)
    (target / 'verified-report.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(['identity', 'status', 'forecast_available', 'reason', 'prediction_epochs'] +
                    [f'{axis}_{measure}' for axis in AXES for measure in
                     ('error_rms_m', 'median_receiver_sigma_m', 'median_abs_error_over_sigma')])
    for task in report['tasks']:
        values = task['metrics'] or {}
        writer.writerow([task['identity'], task['status'], task['forecast_available'], task.get('reason', ''),
                         values.get('prediction_epochs', '')] +
                        [values.get(axis, {}).get(measure, '') for axis in AXES for measure in
                         ('error_rms_m', 'median_receiver_sigma_m', 'median_abs_error_over_sigma')])
    (target / 'per-fit.csv').write_text(buffer.getvalue())
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    args = parser.parse_args()
    report = publish(args.root)
    print(f"{report['forecasts']}/{report['total']} saved ESA forecasts checked; no new fits")


if __name__ == '__main__':
    main()
