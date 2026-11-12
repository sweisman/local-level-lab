# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit the closed receiver-precision holdout without refitting."""

import csv
import gzip
import io
import json
import math
import statistics
from pathlib import Path

from lll.receiver_precision_holdout import join_epochs, summarize
from lll.receiver_precision_holdout_study import (
    STUDY, checked_preparation, recipe)
from lll.studies.artifacts import ArchiveStore, atomic, digest, encoded
from lll.studies.closed import ClosedStudy


MODEL = {0: 'globe with specified field',
         1: 'globe with zero field',
         2: 'stationary disc'}


def linear_trend(joined):
    """Describe a later error's linear trend, without forecasting or refitting."""
    later = [row for row in joined if row['role'] == 'prediction']
    if len(later) < 3:
        raise ValueError('at least three later epochs required')
    times = [float(row['time_s']) for row in later]
    if (not all(math.isfinite(value) for value in times)
            or any(a >= b for a, b in zip(times, times[1:]))):
        raise ValueError('ordered finite later times required')
    center_time = statistics.fmean(times)
    time_sum = math.fsum((value - center_time)**2 for value in times)
    if time_sum <= 0:
        raise ValueError('nonzero later time span required')
    result = {}
    for axis in ('north', 'east', 'height'):
        errors = [float(row[axis + '_error_m']) for row in later]
        if not all(math.isfinite(value) for value in errors):
            raise ValueError('finite later errors required')
        center_error = statistics.fmean(errors)
        slope = math.fsum((time - center_time) * (error - center_error)
                          for time, error in zip(times, errors)) / time_sum
        total = math.fsum((error - center_error)**2 for error in errors)
        remaining = math.fsum((error - center_error -
                               slope * (time - center_time))**2
                              for time, error in zip(times, errors))
        result[axis] = dict(slope_m_per_min=slope * 60,
                            centered_variance_explained=(
                                max(0., min(1., 1. - remaining / total))
                                if total > 0 else None),
                            prediction_epochs=len(later))
    return result


def audit(root):
    root = Path(root).resolve()
    preparation = checked_preparation(root)
    closed = ClosedStudy(root, 'data/' + STUDY)
    pilot = ClosedStudy(root, recipe()['pilot'])
    try:
        if (closed.completion['state'] != 'complete'
                or closed.summary['completed'] != 3
                or closed.summary['charged'] != dict(
                    native_calls=0, packet_visits=0,
                    bound_calls=0, bound_steps=0)
                or set(closed.tasks) != set(preparation['segments'])):
            raise ValueError('closed zero-fit three-task comparison required')
        source = []
        for sid in sorted(closed.tasks):
            result = closed.envelope(sid)['result']
            if (result.get('passed') is not True
                    or result.get('model_fits') != 0
                    or result.get('original_imu_reads') != 0
                    or result.get('protected_esa_reads') != 0):
                raise ValueError('complete saved-data task required')
            material = json.loads(gzip.decompress(
                closed.input('material-' + sid, raw=True)))
            positions = list(csv.DictReader(io.StringIO(gzip.decompress(
                closed.input('positions-' + sid, raw=True)).decode())))
            reported = closed.artifact(sid, 'precision-comparison.json')
            expected = [row for row in preparation['primaries']
                        if row['segment_id'] == sid]
            if len(reported) != 12 or len(expected) != 12:
                raise ValueError('all twelve settings per recording required')
            for row, selection in zip(reported, expected):
                if any(row.get(key) != value for key, value in
                       selection.items()):
                    raise ValueError('training-only selected setting changed')
                identity = row['chosen_identity']
                if identity is None:
                    if row['report'] is not None:
                        raise ValueError('unqualified start gained a report')
                    source.append(dict(**selection, report=None,
                                       accuracy_screen=None, trend=None))
                    continue
                joined = join_epochs(
                    material['selected_epochs'][identity], positions,
                    origin_utc_week_s=material['origin_utc_week_s'],
                    expected_gps_week=material['gps_week'],
                    training_coordinates=material['training_gps'])
                saved = json.loads(gzip.decompress(closed.artifact(
                    sid, 'matched-' + identity + '.json.gz', raw=True)))
                if saved != joined or row['report'] != summarize(joined):
                    raise ValueError('saved matched epochs or descriptive metrics changed')
                original = pilot.envelope(identity)['result']
                if not (original.get('converged') is True
                        and original.get('all_active_columns_retained') is True):
                    raise ValueError('selected pilot start no longer qualified')
                source.append(dict(**selection, report=row['report'],
                                   accuracy_screen=original['accuracy_screen'],
                                   trend=linear_trend(joined)))
        if (len(source) != 36
                or sum(row['report'] is not None for row in source) != 28
                or sum(row['report'] is None for row in source) != 8):
            raise ValueError('complete 28/8 numerical coverage required')
        by_model = []
        for model, label in MODEL.items():
            selected = [row for row in source
                        if row['model'] == model and row['report'] is not None]
            by_model.append(dict(
                model=model, label=label, qualified=len(selected),
                accuracy_screen_passed=sum(
                    row['accuracy_screen']['passed'] is True
                    for row in selected),
                median_later_error_rms_m={axis: statistics.median(
                    row['report'][axis]['error_rms_m'] for row in selected)
                    for axis in ('north', 'east', 'height')},
                median_normalized_rms={axis: statistics.median(
                    row['report'][axis]['normalized_rms'] for row in selected)
                    for axis in ('north', 'east', 'height')},
                median_linear_trend_variance_explained={
                    axis: statistics.median(
                        row['trend'][axis]['centered_variance_explained']
                        for row in selected if row['trend'][axis][
                            'centered_variance_explained'] is not None)
                    for axis in ('north', 'east', 'height')}))
        return dict(version='receiver-precision-holdout-audit-v1',
                    audit_source_sha256=digest(Path(__file__).read_bytes()),
                    study='data/' + STUDY,
                    study_manifest_sha256=closed.completion['manifest_sha256'],
                    study_summary_sha256=closed.completion['summary_sha256'],
                    pilot_manifest_sha256=preparation['pilot_manifest_sha256'],
                    pilot_summary_sha256=preparation['pilot_summary_sha256'],
                    completed_tasks=3, settings=36,
                    numerically_qualified_primaries=28,
                    no_qualified_start=8, by_model=by_model,
                    settings_detail=source,
                    receiver_sigma_is_self_reported=True,
                    absolute_accuracy_calibrated=False,
                    scientific_decision='abstain',
                    new_model_fits=0, original_imu_reads=0,
                    protected_esa_reads=0)
    finally:
        closed.close()
        pilot.close()


def publish(root):
    root = Path(root).resolve()
    result = audit(root)
    destination = root / 'docs/receiver-precision-holdout'
    atomic(destination / 'verified-report.json', encoded(result))
    lines = [
        '# Withheld prediction errors and receiver-reported precision', '',
        'This saved-data check uses the three recordings already selected for '
        'the retrospective prediction pilot. It ran no new model fits. '
        'Each setting chose a numerical start using the earlier training cost '
        'alone; later errors did not choose the start.', '',
        '**Result:** all saved epochs matched that recording’s primary '
        'receiver precision report. Of 36 model, timing and processing '
        'settings, 28 had a numerically qualified start and eight did not. '
        'The receiver’s stated precision is its own estimate, not a measured '
        'truth error. Dividing prediction error by that estimate describes '
        'scale; it does not establish statistical significance.', '',
        '| Model | Qualified / 12 | Passed earlier uncalibrated accuracy screen | '
        'Median later north / east / height RMS (m) | Median error / '
        'receiver-reported sigma, north / east / height |',
        '|---|---:|---:|---:|---:|']
    for row in result['by_model']:
        error = row['median_later_error_rms_m']
        normalized = row['median_normalized_rms']
        lines.append(
            f"| {row['label']} | {row['qualified']} / 12 | "
            f"{row['accuracy_screen_passed']} | "
            f"{error['north']:.2f} / {error['east']:.2f} / "
            f"{error['height']:.2f} | "
            f"{normalized['north']:.1f} / {normalized['east']:.1f} / "
            f"{normalized['height']:.1f} |")
    globe = result['by_model'][0]
    trend = globe['median_linear_trend_variance_explained']
    lines.extend(['',
        'In the nine numerically qualified specified-field globe settings, a '
        'straight time trend accounts for a median '
        f"{trend['north']:.1%} north, {trend['east']:.1%} east and "
        f"{trend['height']:.1%} height of the *centered* later-error "
        'variation. This is a retrospective description across three '
        'recordings. It does not show that a trend could be predicted from '
        'earlier observations, or identify whether IMU drift, motion, timing '
        'or receiver error caused it.', '',
        'These are descriptive medians across different recordings and '
        'settings, including models that may be wrong. Individual settings '
        'and numerical abstentions remain in the verified report. The '
        'per-setting `autocorrelation` fields there are Pearson correlations '
        'between lagged slices; the earlier pilot error-structure report uses '
        'a different full-window normalization. Do not compare those numbers '
        'directly. The '
        'reported receiver precision does not include IMU, calibration, '
        'model or shared navigation errors. This study therefore makes no '
        'positive scientific decision and does not calibrate an absolute '
        'goodness-of-fit test.', '',
        'The zero-fit study, exact selected starts, matched epochs, source '
        'hashes and recovery evidence are retained in the repository’s '
        'study archive. Re-run the auditor with '
        '`~/venv/bin/python -m lll.receiver_precision_holdout_audit`.', ''])
    atomic(destination / 'README.md', '\n'.join(lines).encode())
    return result


def verify_publication(root):
    """Check a compacted study receipt with one archive-index read."""
    root = Path(root).resolve()
    prefix = 'docs/receiver-precision-holdout/recorded-study'
    receipt = json.loads((root / prefix / 'evidence-receipt.json').read_bytes())
    store = ArchiveStore(root)
    try:
        catalog = store.catalog()
        archived = 0
        for relative, expected in receipt['artifacts'].items():
            name = prefix + '/' + relative
            data = store._read(name, catalog)
            if digest(data) != expected:
                raise ValueError('published evidence differs: ' + name)
            archived += name in catalog['paths']
        return dict(verified_artifacts=len(receipt['artifacts']),
                    archived_artifacts=archived)
    finally:
        store.close()


if __name__ == '__main__':
    result = publish(Path(__file__).resolve().parents[2])
    print(json.dumps(dict(completed_tasks=result['completed_tasks'],
                          numerically_qualified_primaries=result[
                              'numerically_qualified_primaries'],
                          no_qualified_start=result['no_qualified_start']),
                     sort_keys=True))
