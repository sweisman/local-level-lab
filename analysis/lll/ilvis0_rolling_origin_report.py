# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify and describe sealed rolling-origin NASA development forecasts."""
import argparse
import csv
import hashlib
import io
import math
import statistics
from pathlib import Path

from lll.studies.artifacts import atomic, encoded
from lll.studies.closed import ClosedStudy
from lll.ilvis0_prediction_growth_audit import horizon_quarters
from lll.ilvis0_saved_prediction import summarize


STUDY = 'data/ilvis0-rolling-origin-development-v1'
MANIFEST_SHA256 = 'dc7fded1b06b068f112e9915114e60b19dbd1ddd2022e84f3b173f19e35b2373'
AXES = ('north', 'east', 'vertical')
QUALIFICATION = 'docs/prediction-rolling-origin/report-qualification-v2-request.json'
REQUIRED_TESTS = (
    'test_primary_uses_training_cost_even_if_later_error_is_worse',
    'test_transfer_preserves_abstention_and_matched_ratio',
    'test_transfer_rejects_nonfinite_saved_error',
    'test_selected_detail_reduces_saved_epochs_and_checks_score',
    'test_fit_audit_keeps_failed_starts_and_bound_activity',
    'test_publication_requires_complete_grid_and_keeps_abstentions',
)


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root, [
        'analysis/lll/ilvis0_rolling_origin_report.py',
        'analysis/lll/ilvis0_prediction_growth_audit.py',
        'analysis/lll/ilvis0_saved_prediction.py',
        'analysis/tests/test_ilvis0_rolling_origin_report.py'])


def selected_detail(epochs, score):
    """Verify the saved score and describe its equal-count withheld quarters."""
    cut = sum(row['role'] == 'training' for row in epochs)
    replay = summarize(epochs, training_epochs=cut,
                       prediction_epochs=len(epochs)-cut)
    if replay != score:
        raise ValueError('saved epoch reduction differs from score')
    prediction = replay['prediction']
    return dict(quarters=horizon_quarters(epochs),
                mean_north_m=prediction['mean_north_m'],
                mean_east_m=prediction['mean_east_m'],
                mean_up_m=prediction['mean_up_m'],
                final_horizontal_m=prediction['final_horizontal_m'],
                final_signed_up_m=prediction['final_signed_up_m'],
                maximum_horizontal_m=prediction['maximum_horizontal_m'],
                maximum_absolute_up_m=prediction['maximum_absolute_up_m'])


def fit_audit_row(case, fit):
    """Retain each start's stopping and normalized-bound status."""
    parameters = None if fit is None else fit.get('normalized_parameters')
    if parameters is not None and any(
            not isinstance(value, (int, float)) or not math.isfinite(value)
            or abs(value) > 1.000001 for value in parameters):
        raise ValueError('finite feasible saved normalized parameters required')
    return dict(identity=case['identity'], segment_id=case['segment_id'],
                origin=case['origin'], profile=case['profile'],
                clock=case['clock'], start=case['start'],
                passed=case['passed'],
                converged=None if fit is None else fit.get('converged'),
                termination=None if fit is None else fit.get('termination'),
                evaluations=None if fit is None else fit.get('evaluations'),
                training_cost=case['training_cost'],
                normalized_parameters_at_bound=(None if parameters is None else
                    sum(abs(value) >= 1.-1e-6 for value in parameters)))


def select_primary(cases):
    """Use earlier training cost only; fixed start breaks exact ties."""
    eligible = []
    for case in cases:
        if not case['passed']:
            continue
        cost = case['training_cost']
        if not isinstance(cost, (int, float)) or not math.isfinite(cost) or cost < 0:
            raise ValueError('finite training cost required for passing fit')
        eligible.append((cost, case['start'], case))
    return min(eligible, key=lambda item: item[:2])[2] if eligible else None


def transfer_rows(cases):
    groups = {}
    for case in cases:
        key = (case['segment_id'], case['profile'], case['clock'])
        origin = case['origin']
        if origin not in ('inner', 'outer'):
            raise ValueError('declared rolling origin required')
        groups.setdefault(key, {}).setdefault(origin, []).append(case)
    output = []
    for (segment, profile, clock), origins in sorted(groups.items()):
        if set(origins) != {'inner', 'outer'} or any(
                sorted(item['start'] for item in values) != [0, 1]
                for values in origins.values()):
            raise ValueError('both starts at both origins required')
        inner = select_primary(origins['inner'])
        outer = select_primary(origins['outer'])
        status = ('matched' if inner and outer else
                  'abstain_both' if not inner and not outer else
                  'abstain_inner' if not inner else 'abstain_outer')
        row = dict(segment_id=segment, profile=profile, clock=clock,
                   status=status,
                   inner_identity=None if inner is None else inner['identity'],
                   outer_identity=None if outer is None else outer['identity'])
        for name, case in (('inner', inner), ('outer', outer)):
            detail = None if case is None else case.get('detail')
            if detail is not None:
                for key, value in detail.items():
                    if key == 'quarters':
                        for index, quarter in enumerate(value, 1):
                            row[f'{name}_quarter_{index}_epochs'] = quarter['epochs']
                            for axis in ('north', 'east', 'up'):
                                row[f'{name}_quarter_{index}_{axis}_rms_m'] = quarter[axis+'_rms_m']
                    else:
                        row[name+'_'+key] = value
        for axis in AXES:
            name = axis+'_rms_m'
            earlier = None if inner is None else inner['prediction'][name]
            later = None if outer is None else outer['prediction'][name]
            if any(not isinstance(value, (int, float)) or
                   not math.isfinite(value) or value < 0
                   for value in (earlier, later) if value is not None):
                raise ValueError('finite nonnegative saved RMS required')
            row[axis+'_inner_rms_m'] = earlier
            row[axis+'_outer_rms_m'] = later
            row[axis+'_ratio'] = (later/earlier if
                                  earlier is not None and earlier > 0 and
                                  later is not None else None)
        output.append(row)
    return output


def build(root='.'):
    root = Path(root).resolve()
    from lll.ilvis0_control_shards import runtime_environment
    from lll.studies.qualification import checked
    request, qualification = checked(
        root, QUALIFICATION, sources=qualification_sources(root),
        environment=runtime_environment(), required_tests=REQUIRED_TESTS,
        minimum_tests=len(REQUIRED_TESTS))
    study = ClosedStudy(root, STUDY)
    try:
        if (study.completion['manifest_sha256'] != MANIFEST_SHA256 or
                study.completion['state'] not in ('complete', 'terminal') or
                len(study.tasks) != 48 or len(study.rows) != 48 or
                study.manifest['allocation']['total'] != 4 or
                study.manifest['limits']['maximum_identities'] != 48 or
                study.manifest['scope'] !=
                'same-source inner/outer NASA development forecasts; '
                'no originals, protected groups or scientific decision'):
            raise ValueError('exact completed finite development study required')
        cases = []
        audit = []
        for identity in study.tasks:
            task = study.tasks[identity]
            row = study.rows[identity]
            result = study.envelope(identity)['result']
            payload = task['payload']
            case = dict(identity=identity, segment_id=payload['segment_id'],
                        origin=payload['origin'], profile=payload['profile'],
                        clock=payload['clock'], start=payload['start'],
                        passed=row['passed'],
                        training_cost=result.get('training_cost'),
                        prediction=result.get('prediction'))
            if row['passed']:
                score = study.artifact(identity, 'scores.json')
                if (result['scientific_decision'] != 'abstain' or
                        result['prediction'] != score['prediction'] or
                        result['training'] != score['training']):
                    raise ValueError('saved qualified score differs')
                case['detail'] = selected_detail(
                    study.artifact(identity, 'epochs.json'), score)
            fit_path = 'artifacts/'+identity+'/fit.json'
            fit = (study.artifact(identity, 'fit.json') if
                   fit_path in study.envelope(identity)['artifacts'] else None)
            audit.append(fit_audit_row(case, fit))
            cases.append(case)
        rows = transfer_rows(cases)
        if len(rows) != 12 or study.summary['charged']['native_calls'] > 9648:
            raise ValueError('complete task grid and finite charges required')
        source = root/'analysis/lll/ilvis0_rolling_origin_report.py'
        return dict(verified=True, study=STUDY,
                    manifest_sha256=MANIFEST_SHA256,
                    summary_sha256=study.completion['summary_sha256'],
                    reporter_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    publication_request_sha256=hashlib.sha256(request).hexdigest(),
                    publication_tests_sha256=hashlib.sha256(qualification).hexdigest(),
                    tasks=48, passing_tasks=sum(case['passed'] for case in cases),
                    matched_settings=sum(row['status'] == 'matched' for row in rows),
                    native_calls=study.summary['charged']['native_calls'],
                    original_reads=0, protected_reads=0,
                    scientific_decision='abstain', rows=rows,
                    fit_audit=audit)
    finally:
        study.close()


def render(report):
    matched = [row for row in report['rows'] if row['status'] == 'matched']
    lines = ['# Earlier-only forecast-error transfer', '',
             f"**{report['matched_settings']}/12 settings have qualified fits at both cuts.**",
             f"The frozen study returned {report['passing_tasks']}/48 numerically passing tasks",
             f"and charged {report['native_calls']} native calls. These are three",
             'development recordings with repeated clock and processing settings,',
             'not twelve independent flights.', '',
             'Each inner fit uses the first third of receiver positions and predicts',
             'the next third. A separate, same-source fit uses the first two thirds',
             'and predicts an equal-length final period. Neither fit sees its',
             'scoring positions before its forecast is saved.', '']
    if matched:
        lines += ['| Direction | Median later/earlier RMS |', '|---|---:|']
        for axis in AXES:
            values = [row[axis+'_ratio'] for row in matched
                      if row[axis+'_ratio'] is not None]
            label = {'north': 'North', 'east': 'East', 'vertical': 'Height'}[axis]
            lines.append(f'| {label} | '
                         + ('unavailable' if not values else
                            f'{statistics.median(values):.2f}×') + ' |')
        lines.append('')
    lines += ['The [complete setting table](result.csv) includes abstentions,',
              'both selected starts, signed errors, maxima, endpoints and',
              'directional RMS in four successive forecast quarters.',
              'The [fit audit](fit-audit.csv) records all 48 starts, including',
              'failed fits and normalized calibration parameters at a bound.',
              'Ratios describe',
              'transfer within these recordings; they are not confidence',
              'multipliers or an Earth-model decision. Failures and task charges',
              'remain in the sealed study.', '',
              '[Frozen plan](PLAN.md) · [Prediction-error roadmap](../PREDICTION_ERROR_LAW_PLAN.md)']
    return '\n'.join(lines)+'\n'


def csv_bytes(report):
    fields = ['segment_id', 'profile', 'clock', 'status',
              'inner_identity', 'outer_identity']
    for axis in AXES:
        fields += [axis+suffix for suffix in
                   ('_inner_rms_m', '_outer_rms_m', '_ratio')]
    for origin in ('inner', 'outer'):
        fields += [origin+'_'+name for name in
                   ('mean_north_m', 'mean_east_m', 'mean_up_m',
                    'final_horizontal_m', 'final_signed_up_m',
                    'maximum_horizontal_m', 'maximum_absolute_up_m')]
        fields += [f'{origin}_quarter_{quarter}_{axis}_rms_m'
                   for quarter in range(1, 5)
                   for axis in ('north', 'east', 'up')]
        fields += [f'{origin}_quarter_{quarter}_epochs'
                   for quarter in range(1, 5)]
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(report['rows'])
    return stream.getvalue().encode()


def audit_csv_bytes(report):
    fields = ['identity', 'segment_id', 'origin', 'profile', 'clock',
              'start', 'passed', 'converged', 'termination', 'evaluations',
              'training_cost', 'normalized_parameters_at_bound']
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(report['fit_audit'])
    return stream.getvalue().encode()


def publish(root='.'):
    root = Path(root).resolve()
    report = build(root)
    directory = root/'docs/prediction-rolling-origin'
    atomic(directory/'RESULT.md', render(report).encode())
    atomic(directory/'result.csv', csv_bytes(report))
    atomic(directory/'fit-audit.csv', audit_csv_bytes(report))
    atomic(directory/'verified-report.json', encoded(report))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    args = parser.parse_args()
    report = publish(args.root)
    print(f"{report['passing_tasks']}/48 tasks passed; "
          f"{report['matched_settings']}/12 matched settings")


if __name__ == '__main__':
    main()
