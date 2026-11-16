# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only three-model audit of the opened ESA 400/120 development cut."""

import csv
import gzip
import hashlib
import io
import json
import math
from pathlib import Path

from .esa_rolling_origin_400_model_matrix import ID, LAWS, MODELS, tasks


def compare(rows, *, profile, law):
    """Select from training only; abstain if a candidate's primary is unknown."""
    if type(profile) is not bool or law not in LAWS:
        raise ValueError('declared profile and error convention required')
    selected = [row for row in rows if row['profile'] is profile and
                row['law'] == law]
    expected = {(model, start) for model in MODELS for start in (0, 1)}
    if (len(selected) != 6 or
            {(row['model'], row['start']) for row in selected} != expected):
        raise ValueError('complete fixed model/start setting required')
    primaries = {}
    for model in MODELS:
        candidates = [row for row in selected if row['model'] == model]
        if not all(row['fit_known'] for row in candidates):
            primaries[model] = None
            continue
        converged = [row for row in candidates if row['converged']]
        primary = min(converged,
                      key=lambda row: (row['training_cost'], row['start'])) \
                      if converged else None
        primaries[model] = (primary if primary is not None and
                            primary['forecast_complete'] else None)
    complete = all(primaries.values())
    result = dict(profile=profile, law=law, complete=complete,
                  primary_start={model: (None if row is None else row['start'])
                                 for model, row in primaries.items()},
                  shape_lower_error_family=None, preferred_model=None,
                  preferred_accuracy=None, field_lower_error_model=None,
                  scientific_decision='abstain')
    if not complete:
        return result
    globe = min((primaries['sphere_rotating'], primaries['sphere_still']),
                key=lambda row: row['prediction_total_rms_m'])
    flat = primaries['flat_still']
    if globe['prediction_total_rms_m'] == flat['prediction_total_rms_m']:
        return result
    preferred = (globe if globe['prediction_total_rms_m'] <
                 flat['prediction_total_rms_m'] else flat)
    result.update(shape_lower_error_family=(
        'globe' if preferred is globe else 'flat'),
        preferred_model=preferred['model'],
        preferred_accuracy=(preferred['training_accuracy'] and
                            preferred['prediction_accuracy']))
    if preferred is globe:
        rotating = primaries['sphere_rotating']['prediction_total_rms_m']
        still = primaries['sphere_still']['prediction_total_rms_m']
        result['field_lower_error_model'] = (
            'specified_field' if rotating < still else
            'zero_field' if still < rotating else None)
    return result


def build(root):
    import numpy as np
    from .airquantumgrav_scoring import receiver_errors, sections
    from .studies.artifacts import digest
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    study = ClosedStudy(root, 'data/'+ID)
    try:
        if (study.summary['completed'] != len(tasks()) or
                study.summary['state'] not in ('complete', 'terminal') or
                set(study.tasks) != {row['identity'] for row in tasks()} or
                digest(Path(__file__).read_bytes()) != study.manifest[
                    'sources']['analysis/lll/esa_rolling_origin_400_model_matrix_report.py']):
            raise ValueError('sealed unchanged 24-case matrix required')
        for name, sha in study.manifest['sources'].items():
            study.read('source-freeze/'+name, sha, raw=True)
        origin = study.input('parent_identity')
        parent = ClosedStudy(root,
            'data/prediction-observed-development-continuation-v1-20261113')
        try:
            if (origin['source_id'] != 'esa-99f1530c3eda4318' or
                    origin['manifest_sha256'] != parent.completion[
                        'manifest_sha256'] or
                    origin['summary_sha256'] != parent.completion['summary_sha256']):
                raise ValueError('opened development parent differs')
            all_rows = json.loads(gzip.decompress(parent.input('training',raw=True)))
            training = json.loads(gzip.decompress(study.input('training',raw=True)))
            times = study.input('forecast_times')
            if (len(all_rows) != 800 or len(training) != 400 or
                    training != all_rows[:400] or len(times) != 520):
                raise ValueError('exact earlier training and withheld support required')
            receiver = np.asarray([[math.radians(row['latitude_deg']),
                math.radians(row['longitude_deg']), row['height_m']]
                for row in all_rows[:520]], dtype=float)
            rows = []
            for task in tasks():
                spec = task['payload']
                identity = task['identity']
                outcome = study.rows[identity]
                row = dict(identity=identity, **spec, fit_known=False,
                    converged=False, training_cost=None,
                    forecast_complete=False, training_accuracy=False,
                    prediction_accuracy=False, prediction_total_rms_m=None,
                    prediction_horizontal_rms_m=None,
                    prediction_vertical_rms_m=None,
                    forecast_sha256=None, failure_status=outcome['status'])
                if outcome['status'] != 'complete':
                    rows.append(row)
                    continue
                result = study.envelope(identity)['result']
                fit = study.artifact(identity, 'fit.json')
                score = fit.get('gaussian_training_score', {})
                cost = score.get('negative_log_likelihood')
                if (fit.get('model') != spec['model'] or
                        result.get('model') != spec['model'] or
                        result.get('profile') is not spec['profile'] or
                        result.get('law') != spec['law'] or
                        result.get('start') != spec['start'] or
                        type(cost) not in (int, float) or
                        not math.isfinite(cost) or
                        fit.get('prediction_receiver_positions_used_in_training')
                            is not False):
                    raise ValueError('sealed fit identity or training cost differs')
                row.update(fit_known=True, converged=fit['converged'],
                           training_cost=float(cost))
                if not result['passed']:
                    rows.append(row)
                    continue
                forecast_raw = study.artifact(identity, 'forecast.json', raw=True)
                forecast = json.loads(forecast_raw)
                if (forecast['training_epochs'] != 400 or
                        forecast['prediction_epochs'] != 120 or
                        forecast['prediction_receiver_positions_used'] is not False or
                        forecast['times_s'] != times or
                        len(forecast['coordinates']) != 520):
                    raise ValueError('complete earlier-only forecast required')
                errors = receiver_errors(forecast['coordinates'], receiver)
                assessed = sections(errors, 400)
                train, later = assessed['training'], assessed['prediction']
                row.update(forecast_complete=True,
                    training_accuracy=train['accuracy']['passed'],
                    prediction_accuracy=later['accuracy']['passed'],
                    prediction_total_rms_m=later['total_rms_m'],
                    prediction_horizontal_rms_m=later['horizontal_rms_m'],
                    prediction_vertical_rms_m=later['vertical_rms_m'],
                    forecast_sha256=hashlib.sha256(forecast_raw).hexdigest())
                rows.append(row)
            settings = [compare(rows, profile=profile, law=law)
                        for profile in (False, True) for law in LAWS]
            return dict(version='esa-400-120-model-matrix-report-v1',
                study_id=ID, completed=study.summary['completed'],
                technical_passes=sum(row['forecast_complete'] for row in rows),
                total=len(rows), rows=rows, settings=settings,
                complete_settings=sum(item['complete'] for item in settings),
                fit_manifest_sha256=study.completion['manifest_sha256'],
                fit_summary_sha256=study.completion['summary_sha256'],
                parent_manifest_sha256=parent.completion['manifest_sha256'],
                source_sha256=digest(Path(__file__).read_bytes()),
                original_reads=0, protected_reads=0,
                independent_validation=False, aircraft_error_law_qualified=False,
                statistical_significance_established=False,
                scientific_decision='abstain')
        finally:
            parent.close()
    finally:
        study.close()


def publish(root):
    from .studies.artifacts import atomic, encoded

    result = build(root)
    base = Path(root).resolve()/'docs/prediction-observed-development'
    atomic(base/'ESA_400_120_MODEL_MATRIX_RESULT.json', encoded(result))
    for name, entries, fields in (
            ('ESA_400_120_MODEL_MATRIX_FITS.csv', result['rows'],
             ('identity', 'model', 'profile', 'law', 'start', 'fit_known',
              'converged', 'training_cost', 'forecast_complete',
              'training_accuracy', 'prediction_accuracy',
              'prediction_total_rms_m', 'prediction_horizontal_rms_m',
              'prediction_vertical_rms_m', 'failure_status')),
            ('ESA_400_120_MODEL_MATRIX_SETTINGS.csv', result['settings'],
             ('profile', 'law', 'complete', 'shape_lower_error_family',
              'preferred_model', 'preferred_accuracy',
              'field_lower_error_model'))):
        output = io.StringIO(newline='')
        writer = csv.DictWriter(output, fieldnames=fields,
                                extrasaction='ignore', lineterminator='\n')
        writer.writeheader()
        writer.writerows(entries)
        atomic(base/name, output.getvalue().encode())
    lines = ['# Matched ESA development forecasts', '',
        '**{}/24** fit tasks closed; **{}/4** settings have all three'.format(
            result['completed'], result['complete_settings']),
        'training-selected forecasts.', '',
        '| Processing case | IMU error convention | Complete | Lower-error shape | Preferred fit adequate? | Background-field comparison |',
        '|---|---|---|---|---|---|']
    for item in result['settings']:
        lines.append('| {} | {} | {} | {} | {} | {} |'.format(
            'Profiled' if item['profile'] else 'Zero removal',
            item['law'], 'Yes' if item['complete'] else 'No',
            item['shape_lower_error_family'] or 'Unresolved',
            ('Yes' if item['preferred_accuracy'] else 'No')
                if item['complete'] else 'Unavailable',
            item['field_lower_error_model'] or 'Not assessed'))
    lines += ['', 'These are numerical comparisons on one already opened',
        'development flight, with no later receiver position in fitting.',
        'The horizon was chosen after earlier outcomes were known. Fit',
        'convergence and physical accuracy are reported separately; no',
        'aircraft error range or scientific decision is calibrated.',
        'The seven reserved ESA flight groups remain closed.', '',
        '[All fits](ESA_400_120_MODEL_MATRIX_FITS.csv) ·',
        '[Matched settings](ESA_400_120_MODEL_MATRIX_SETTINGS.csv) ·',
        '[Frozen plan](ESA_400_120_MODEL_MATRIX_PLAN.md).', '']
    atomic(base/'ESA_400_120_MODEL_MATRIX_RESULT.md', '\n'.join(lines).encode())
    return result


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('audit', 'publish'))
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    result = publish(args.root) if args.action == 'publish' else build(args.root)
    print(json.dumps({key: result[key] for key in (
        'completed', 'technical_passes', 'complete_settings',
        'scientific_decision')}, sort_keys=True))


if __name__ == '__main__':
    main()
