# SPDX-License-Identifier: AGPL-3.0-or-later
"""Describe dependence in sealed ESA development forecast errors, without refits."""
import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import statistics
from pathlib import Path

from lll.esa_saved_precision_audit import (
    PARENT, MANIFEST_SHA256, SUMMARY_SHA256, SCORING_SHA256, AXES, summarize)
from lll.studies.closed import ClosedStudy

LAGS = (1, 5, 20, 60)


def _correlation(left, right):
    if len(left) != len(right) or len(left) < 3:
        return None
    if any(not math.isfinite(value) for value in (*left, *right)):
        raise ValueError('finite residuals required')
    for series in (left, right):
        if max(series) - min(series) <= 1e-12 * max(1., max(map(abs, series))):
            return None
    a = statistics.fmean(left)
    b = statistics.fmean(right)
    da = [value - a for value in left]
    db = [value - b for value in right]
    return sum(x*y for x, y in zip(da, db, strict=True)) / math.sqrt(
        sum(x*x for x in da) * sum(y*y for y in db))


def summarize_structure(scores, receiver_rows, *, training_epochs, lags=LAGS):
    """Measure withheld-error drift and dependence after the exact epoch join."""
    checked = summarize(scores, receiver_rows, training_epochs=training_epochs)
    count = checked['prediction_epochs']
    if (not isinstance(lags, tuple) or not lags or
            any(type(lag) is not int or lag < 1 or lag > count-3 for lag in lags) or
            len(set(lags)) != len(lags)):
        raise ValueError('lags must be distinct and leave three matched pairs')
    times = scores['times_s'][training_epochs:]
    gaps = [right-left for left, right in zip(times[:-1], times[1:], strict=True)]
    if any(not math.isclose(gap, 1., rel_tol=0., abs_tol=.002)
           for gap in gaps):
        raise ValueError('approximately one-second withheld receiver cadence required')
    centered_time = [value-statistics.fmean(times) for value in times]
    time_ss = sum(value*value for value in centered_time)
    if time_ss <= 0:
        raise ValueError('distinct withheld times required')
    errors = scores['errors_neu_m'][training_epochs:]
    result = dict(prediction_epochs=count, lags_epochs=list(lags),
                  receiver_gap_min_s=min(gaps),
                  receiver_gap_median_s=statistics.median(gaps),
                  receiver_gap_max_s=max(gaps), axes={},
                  cross_axis_raw={}, cross_axis_detrended={},
                  scientific_decision='abstain')
    raw, detrended = {}, {}
    for axis, name in enumerate(AXES):
        values = [row[axis] for row in errors]
        earlier = [row[axis] for row in scores['errors_neu_m'][:training_epochs]]
        training_rms = math.sqrt(statistics.fmean(value*value for value in earlier))
        withheld_rms = math.sqrt(statistics.fmean(value*value for value in values))
        mean = statistics.fmean(values)
        slope = sum(t*(value-mean) for t, value in
                    zip(centered_time, values, strict=True)) / time_ss
        remainder = [value-mean-slope*t for value, t in
                     zip(values, centered_time, strict=True)]
        raw[name], detrended[name] = values, remainder
        result['axes'][name] = dict(
            training_rms_m=training_rms, withheld_rms_m=withheld_rms,
            withheld_to_training_rms=(withheld_rms/training_rms
                                      if training_rms > 0 else None),
            mean_error_m=mean, slope_m_per_minute=slope*60.,
            raw_lag_correlation={str(lag): _correlation(values[:-lag], values[lag:])
                                 for lag in lags},
            detrended_lag_correlation={
                str(lag): _correlation(remainder[:-lag], remainder[lag:])
                for lag in lags})
    for index, left in enumerate(AXES):
        for right in AXES[index+1:]:
            key = left+':'+right
            result['cross_axis_raw'][key] = _correlation(raw[left], raw[right])
            result['cross_axis_detrended'][key] = _correlation(
                detrended[left], detrended[right])
    return result


def build(root):
    root = Path(root).resolve()
    study = ClosedStudy(root, PARENT)
    try:
        if (study.completion['state'] != 'terminal' or
                study.completion['manifest_sha256'] != MANIFEST_SHA256 or
                study.completion['summary_sha256'] != SUMMARY_SHA256 or
                study.manifest['inputs']['scoring']['sha256'] != SCORING_SHA256 or
                len(study.tasks) != 24 or len(study.rows) != 24 or
                sum(row['passed'] for row in study.rows.values()) != 22):
            raise ValueError('exact sealed ESA development parent required')
        receiver_rows = json.loads(gzip.decompress(study.input('scoring', raw=True)))
        if len(receiver_rows) != 1200:
            raise ValueError('1200 sealed receiver epochs required')
        tasks = []
        for identity in study.tasks:
            row = study.rows[identity]
            model = study.tasks[identity]['payload']['model']
            if model not in ('sphere_rotating', 'sphere_still', 'flat_still'):
                raise ValueError('unexpected frozen physical model')
            item = dict(identity=identity, model=model, status=row['status'],
                        passed=row['passed'], structure=None)
            if row['passed']:
                forecast = study.artifact(identity, 'forecast.json')
                if forecast['training_epochs'] != 800 or forecast['prediction_epochs'] != 400:
                    raise ValueError('unchanged 800/400 forecast split required')
                item['structure'] = summarize_structure(
                    study.artifact(identity, 'scores.json'), receiver_rows,
                    training_epochs=800)
            else:
                item['reason'] = study.envelope(identity)['result'].get('reason')
            tasks.append(item)
        source = root / 'analysis/lll/esa_saved_error_structure.py'
        return dict(verified=True, parent=PARENT,
                    parent_manifest_sha256=MANIFEST_SHA256,
                    parent_summary_sha256=SUMMARY_SHA256,
                    scoring_sha256=SCORING_SHA256,
                    reporter_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    tasks=tasks, total=len(tasks),
                    forecasts=sum(item['structure'] is not None for item in tasks),
                    native_calls=0, original_reads=0, protected_reads=0,
                    scientific_decision='abstain')
    finally:
        study.close()


def render(report):
    if report.get('verified') is not True or report['forecasts'] != 22:
        raise ValueError('verified 22-forecast saved audit required')
    available = [item['structure'] for item in report['tasks']
                 if item['structure'] is not None]
    lines = ['# Dependence in the ESA development forecasts', '',
             'This check reads the 22 sealed forecasts from one development',
             'recording. It makes no new fits and reads no reserved confirmation',
             'group. The two unfinished original fits remain visible in the',
             '[per-fit table](error-structure.csv).', '',
             'The table reports median correlation of later prediction errors',
             'across the 22 fits. The last two columns remove each fit’s',
             'straight-line trend first. This describes the errors;',
             'it does not fit or validate a covariance law.', '',
             '| Direction | Raw, 1 epoch apart | Detrended, 1 epoch apart | Detrended, 60 epochs apart |',
             '|---|---:|---:|---:|']
    for axis in AXES:
        def median(kind, lag):
            values = [item['axes'][axis][kind][str(lag)] for item in available]
            values = [value for value in values if value is not None]
            return 'unavailable' if not values else f'{statistics.median(values):.6f}'
        lines.append(f'| {axis.capitalize()} | {median("raw_lag_correlation", 1)} '
                     f'| {median("detrended_lag_correlation", 1)} '
                     f'| {median("detrended_lag_correlation", 60)} |')
    lines += ['', 'The next table compares later forecast RMS with the RMS of',
              'residuals from the earlier period used to fit each model. It is',
              'the median ratio across completed settings of the same candidate.',
              'The earlier residuals are **in sample**; these ratios are a',
              'diagnostic of forecast growth, not uncertainty multipliers.', '',
              '| Candidate | Forecasts | North | East | Height |',
              '|---|---:|---:|---:|---:|']
    for model, label in (('sphere_rotating', 'Globe + specified field'),
                         ('sphere_still', 'Globe + zero field'),
                         ('flat_still', 'Tested flat disc')):
        selected = [item['structure'] for item in report['tasks']
                    if item['model'] == model and item['structure'] is not None]
        ratios = []
        for axis in AXES:
            values = [value['axes'][axis]['withheld_to_training_rms']
                      for value in selected]
            values = [value for value in values if value is not None]
            ratios.append('unavailable' if not values else
                          f'{statistics.median(values):.1f}×')
        lines.append(f'| {label} | {len(selected)} | '
                     + ' | '.join(ratios) + ' |')
    lines += ['', 'On this development recording, a fixed forecast-error scale',
              'taken from the fitted training residual RMS would miss the',
              'large growth during prediction. The ratios do not identify',
              'which instrument or motion error caused that growth.']
    gaps = [item['receiver_gap_median_s'] for item in available]
    lines += ['', f'The median receiver gap is {statistics.median(gaps):.6f} seconds;',
              'every gap lies within 0.002 seconds of one second. Thus one',
              'and 60 epochs correspond approximately to one and 60 seconds.',
              'Each fit has 400 later receiver epochs. Those',
              'epochs share the same earlier fitted calibration and IMU',
              'forecast; they are not 400 independent trials. Trend removal',
              'is diagnostic, not a model correction or coverage claim.',
              'A usable aircraft error law still needs training-only estimation',
              'and independent prediction checks.', '',
              '[Receiver precision comparison](README.md) ·',
              '[Prediction uncertainty roadmap](../PREDICTION_ERROR_LAW_PLAN.md)']
    return '\n'.join(lines)+'\n'


def csv_bytes(report):
    fields = ['identity', 'model', 'status', 'passed', 'reason', 'prediction_epochs']
    for axis in AXES:
        fields += [f'{axis}_{name}' for name in (
            'training_rms_m', 'withheld_rms_m', 'withheld_to_training_rms',
            'mean_error_m', 'slope_m_per_minute',
            *(f'{kind}_lag{lag}' for lag in LAGS for kind in ('raw', 'detrended')))]
    fields += ['detrended_'+pair for pair in
               ('north:east', 'north:height', 'east:height')]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    for task in report['tasks']:
        row = {key: task.get(key) for key in fields}
        value = task['structure']
        if value is not None:
            row['prediction_epochs'] = value['prediction_epochs']
            for axis in AXES:
                stats = value['axes'][axis]
                for name in ('training_rms_m', 'withheld_rms_m',
                             'withheld_to_training_rms'):
                    row[f'{axis}_{name}'] = stats[name]
                row[f'{axis}_mean_error_m'] = stats['mean_error_m']
                row[f'{axis}_slope_m_per_minute'] = stats['slope_m_per_minute']
                for lag in LAGS:
                    row[f'{axis}_raw_lag{lag}'] = stats['raw_lag_correlation'][str(lag)]
                    row[f'{axis}_detrended_lag{lag}'] = (
                        stats['detrended_lag_correlation'][str(lag)])
            for pair, correlation in value['cross_axis_detrended'].items():
                row['detrended_'+pair] = correlation
        writer.writerow(row)
    return output.getvalue().encode()


def publish(root):
    from lll.studies.artifacts import atomic, encoded
    report = build(root)
    target = Path(root) / 'docs/esa-prediction-error-scale'
    atomic(target / 'CORRELATION.md', render(report).encode())
    atomic(target / 'error-structure.csv', csv_bytes(report))
    atomic(target / 'error-structure-verified.json', encoded(report))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    args = parser.parse_args()
    report = publish(args.root)
    print(f"{report['forecasts']}/{report['total']} sealed forecasts audited; no fits")


if __name__ == '__main__':
    main()
