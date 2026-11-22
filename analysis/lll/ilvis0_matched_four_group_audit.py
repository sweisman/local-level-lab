# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify saved matched forecasts and fixed accuracy by NASA flight group."""

import argparse
from contextlib import ExitStack, closing
import json
import math
from pathlib import Path

from .ilvis0_prediction_audit import _errors
from .ilvis0_prediction_observed import accuracy_screen
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


FOLDER = 'docs/ilvis0-measurement-contribution/'
PLAN = FOLDER+'MATCHED_FOUR_GROUP_AUDIT_PLAN.md'
RESULT = FOLDER+'matched-four-group-audit.json'
SELECTION = FOLDER+'matched-pilot-candidates-receipt.json'
SELECTION_SHA = 'd68ce7200bb45cb01b3c421598061a51442ccc52da5bdb7f3ecc9977521f875c'
RECOVERED = 'docs/ilvis0-matched-unstarted-disc-runtime'
EXTENSION_MANIFEST = '0f53e4a4c5f9aa02ebc17fd4356ff1738177bf210a83b8caaaafe62e709075ff'


def disposition(result, *, open_study=False):
    if result is None:
        return 'pending' if open_study else 'unsealed'
    if result.get('error_type') == 'BudgetStopped':
        return 'budget_stopped'
    if result.get('error_type'):
        return 'error'
    if result.get('converged') is False:
        return 'numerical_nonpass'
    if result['passed'] and result.get('converged') and result.get('forecast_saved_before_scoring'):
        return 'scorable'
    return 'forecast_nonpass'


def error_summary(times, errors):
    rows = [dict(zip(('north_direct_error_m', 'east_direct_error_m', 'up_direct_error_m'), row, strict=True))
            for row in errors]
    if (len(rows) != len(times) or not rows or any(not math.isfinite(t) for t in times)
            or any(left >= right for left, right in zip(times, times[1:]))
            or any(not math.isfinite(value) for row in rows for value in row.values())):
        raise ValueError('finite errors on ordered forecast epochs are required')
    by_time = {}
    for time, row in zip(times, rows, strict=True):
        offset = math.floor((time-times[0])/30)*30
        by_time.setdefault(offset, []).append(row)

    def describe(part):
        scored = _errors(part)
        return dict(scored, total_rms_m=math.hypot(scored['horizontal_rms_m'], scored['vertical_rms_m']),
                    mean_neu_m=[math.fsum(r[k] for r in part)/len(part) for k in part[0]])

    result = describe(rows)
    return dict(result, accuracy=accuracy_screen(result),
                windows=[dict(offset_start_s=offset, **describe(part)) for offset, part in by_time.items()])


def replay(study, identity, training, scoring, queries, policy):
    import numpy as np

    from .ilvis0_matched_unstarted_report import forecast_scores
    from .ilvis0_solver_position import physical_metric

    check = forecast_scores(study, identity, scoring, queries, training, policy)
    fit = study.artifact(identity, 'fit.json')
    forecast = study.artifact(identity, 'forecast.json')
    cut = len(training['query_times_s'])
    observed_times = scoring['query_times_s']
    predicted = np.asarray(forecast['coordinates'][cut:], float)
    streams = {}
    for name, coordinates in scoring['coordinates'].items():
        reference = np.asarray(coordinates, float)
        errors = (predicted-reference)*physical_metric(reference)
        if errors.shape != (len(observed_times), 3):
            raise ValueError('every receiver stream must cover exactly the same later epochs')
        streams[name] = error_summary(observed_times, errors.tolist())
    return dict(training_evaluations=check['training_evaluations'], native_calls=check['native_calls'],
        training_cost=fit['residual_sum_squares'], verified_prefix_error_m=check['prefix_error_m'],
        error_scores=streams, heldout_rms_by_gps_stream=check['scores'])


def build(root, *, existing_only=False):
    from . import ilvis0_matched_extension_forecast as extension, ilvis0_matched_unstarted_report as recovered

    raw = (root/SELECTION).read_bytes()
    if digest(raw) != SELECTION_SHA:
        raise ValueError('the unchanged metadata-only flight group selection is required')
    candidates = json.loads(raw)['candidates']
    results = []
    with ExitStack() as stack:
        original = stack.enter_context(closing(ClosedStudy(root, recovered.ARCHIVE)))
        extra = stack.enter_context(closing(ClosedStudy(root, RECOVERED, store=original.store)))
        if ((original.completion['manifest_sha256'], original.completion['summary_sha256']) !=
                (recovered.MANIFEST, recovered.SUMMARY)
                or (extra.completion['manifest_sha256'], extra.completion['summary_sha256']) !=
                (recovered.STAGE_MANIFEST, recovered.STAGE_SUMMARY) or set(extra.rows) != {recovered.IDENTITY}
                or recovered.IDENTITY in original.rows
                or digest(extra.read('completion.json', raw=True)) != recovered.CONTINUATION_SHA
                or extra.manifest['environment'] != original.manifest['environment']
                or any(extra.manifest['inputs'][key]['sha256'] != info['sha256']
                       for key, info in original.manifest['inputs'].items())):
            raise ValueError('exact archived preflight and charged continuation required')
        added = None
        if not existing_only:
            added = stack.enter_context(closing(ClosedStudy(root, 'data/'+extension.ID, store=original.store)))
            if added.completion['manifest_sha256'] != EXTENSION_MANIFEST or len(added.tasks) != 8:
                raise ValueError('exact frozen eight-fit extension required')
        completions = [study.completion for study in (original, extra, added) if study is not None]
        for flight in candidates:
            segment = flight['segment_id']
            base = original if flight['prior_preflight_group'] else added
            attempts, scores = {}, {}
            for model in recovered.MODELS:
                identity = segment+'-'+model
                study = extra if identity == recovered.IDENTITY else base
                envelope = study.envelope(identity) if study is not None and identity in study.rows else None
                outcome = envelope['result'] if envelope else None
                status = disposition(outcome, open_study=study is None)
                row = dict(status=status, original_status=envelope['status'] if envelope else None,
                    charged=envelope['charged'] if envelope else None,
                    failure_type=outcome.get('error_type') if outcome else None)
                if status == 'scorable':
                    training, scoring, queries = (base.input(segment+'-'+name)
                                                   for name in ('training', 'scoring', 'queries'))
                    row.update(replay(study, identity, training, scoring, queries, base.input('recipe')))
                    scores[model] = row
                attempts[model] = row
            comparison = extension.compare_shapes(scores)
            results.append(dict(group_id=flight['group_id'], segment_id=segment, imu_type=flight['imu_type'],
                mean_latitude_deg=flight['mean_latitude_deg'], mean_course_deg=flight['mean_course_deg'],
                duration_s=flight['duration_s'], median_ground_speed_kmh=flight['median_ground_speed_kmh'],
                attempts=attempts, **comparison))
    return dict(groups=results, source_completions=completions, selection_sha256=SELECTION_SHA,
        plan_sha256=digest((root/PLAN).read_bytes()), reporter_sha256=digest(Path(__file__).read_bytes()),
        new_fits=0, new_propagations=0, accuracy_calibrated=False, scientific_decision='abstain')


def main():
    from .ilvis0_matched_observed_inputs import _write_equal

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--existing-only', action='store_true')
    args = parser.parse_args()
    root = Path.cwd()
    result = build(root, existing_only=args.existing_only)
    raw = encoded(result)
    if not args.existing_only:
        _write_equal(root/RESULT, raw)
    summary = []
    for group in result['groups']:
        summary.append(dict(group_id=group['group_id'], imu_type=group['imu_type'], shape=group['shape_by_field'],
            field=group['globe_field'], dispositions={k: row['status'] for k, row in group['attempts'].items()},
            accuracy_by_model={k: {t: v['accuracy']['passed'] for t, v in row['error_scores'].items()}
                               for k, row in group['attempts'].items() if row['status'] == 'scorable'}))
    print(json.dumps(dict(groups=summary, sha256=digest(raw)), sort_keys=True))


if __name__ == '__main__':
    main()
