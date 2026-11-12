# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only four-group forecast transfer report; no fitting or scoring reads."""
import csv
import hashlib
import io
import math
from pathlib import Path


AXES = ('north', 'east', 'vertical')
STUDY = 'data/ilvis0-four-group-transfer-v1'
MANIFEST_SHA256 = '50dde3aba9184032ff81b422df5afbbeb656e7440b85478b3773e696ff8a6182'
QUALIFICATION = 'docs/prediction-group-transfer/report-qualification-request.json'
REQUIRED_TESTS = (
    'test_all_four_groups_remain_in_denominator_and_adequacy_is_separate',
    'test_no_missing_or_duplicate_group_can_inflate_transfer_fraction',
    'test_qualified_row_needs_all_axes_and_maxima',
    'test_missing_first_cut_does_not_hide_available_second_cut',
    'test_render_keeps_stopping_and_coverage_limits_visible',
    'test_publication_rejects_incomplete_parent',
)


def assess_transfer(rows, reference):
    """Count every selected group and keep physical adequacy separate."""
    if (not isinstance(rows, list) or len(rows) != 4 or
            not isinstance(reference, dict) or set(reference) != set(AXES) or
            any(not isinstance(reference[axis], (int, float)) or
                not math.isfinite(reference[axis]) or reference[axis] <= 0
                for axis in AXES)):
        raise ValueError('four selected groups and finite positive reference required')
    seen = set()
    result = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('complete saved group row required')
        segment = row.get('segment_id')
        status = row.get('status')
        if (not isinstance(segment, str) or not segment or segment in seen or
                status not in ('matched', 'abstain_inner',
                               'abstain_outer', 'abstain_both')):
            raise ValueError('unique saved group and valid stopping status required')
        seen.add(segment)
        if status in ('abstain_outer', 'abstain_both'):
            result.append(dict(segment_id=segment, status='abstain',
                               transfer_within_reference=None,
                               physical_screen_passed=None))
            continue
        names = [axis + '_outer_rms_m' for axis in AXES]
        names += ['outer_maximum_horizontal_m', 'outer_maximum_absolute_up_m']
        values = []
        for name in names:
            value = row.get(name)
            if (not isinstance(value, (int, float)) or
                    not math.isfinite(value) or value < 0):
                raise ValueError('finite nonnegative second-cut errors required')
            values.append(float(value))
        north, east, height, max_horizontal, max_up = values
        within = all(value <= reference[axis]
                     for axis, value in zip(AXES, values[:3]))
        adequate = (math.hypot(north, east) <= 10. and height <= 30. and
                    max_horizontal <= 50. and max_up <= 150.)
        result.append(dict(segment_id=segment, status='scored',
                           transfer_within_reference=within,
                           physical_screen_passed=adequate,
                           rms_to_reference={axis: value/reference[axis]
                                             for axis, value in zip(AXES, values[:3])}))
    return dict(version='ilvis0-four-group-transfer-assessment-v1',
                groups=4, transfer_within_reference=sum(
                    row['transfer_within_reference'] is True for row in result),
                physical_screen_passed=sum(
                    row['physical_screen_passed'] is True for row in result),
                abstentions=sum(row['status'] == 'abstain' for row in result),
                group_rows=result, reference_rms_m=dict(reference),
                reference_is_confidence_limit=False,
                coverage_calibrated=False, scientific_decision='abstain')


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root, [
        'analysis/lll/ilvis0_group_transfer_report.py',
        'analysis/tests/test_ilvis0_group_transfer_report.py'])


def build(root='.'):
    """Replay all sealed task scores and the fixed prior reference."""
    from lll.ilvis0_control_shards import runtime_environment
    from lll.ilvis0_rolling_origin_report import (
        fit_audit_row, selected_detail, transfer_rows)
    from lll.prediction_transfer_reference import from_saved_csv
    from lll.studies.artifacts import digest
    from lll.studies.closed import ClosedStudy
    from lll.studies.qualification import checked

    root = Path(root).resolve()
    request, tests = checked(
        root, QUALIFICATION, sources=qualification_sources(root),
        environment=runtime_environment(), required_tests=REQUIRED_TESTS,
        minimum_tests=len(REQUIRED_TESTS))
    study = ClosedStudy(root, STUDY)
    try:
        if (study.completion['state'] not in ('complete', 'terminal') or
                study.completion['manifest_sha256'] != MANIFEST_SHA256 or
                len(study.tasks) != 16 or len(study.rows) != 16 or
                study.manifest['allocation']['total'] != 1 or
                study.manifest['limits']['maximum_identities'] != 16 or
                study.manifest['limits']['native_calls'] != 3216 or
                study.manifest['scope'] !=
                'four preselected retrospective NASA groups; descriptive forecast-error transfer only'):
            raise ValueError('complete exact four-group study required')
        reference_raw = (root/'docs/prediction-rolling-origin/result.csv').read_bytes()
        reference = from_saved_csv(
            reference_raw,
            expected_sha256='651ae7c87d28d4d5e2d4b9493d3f5a990fc550adc1972c30d970e3bc32ac4117')
        if study.input('transfer-reference') != reference:
            raise ValueError('saved reference differs from prior first-cut scores')
        selection_name = 'docs/prediction-group-transfer/selection.csv'
        selection_raw = (root/selection_name).read_bytes()
        receipt = study.input('selection-receipt')
        if digest(selection_raw) != receipt['input_sha256'][selection_name]:
            raise ValueError('preselected group metadata changed')
        selection = list(csv.DictReader(io.StringIO(selection_raw.decode())))
        layouts = study.input('layouts')
        if (len(selection) != len(layouts) or
                [row['segment_id'] for row in selection] !=
                [row['segment_id'] for row in layouts]):
            raise ValueError('saved group order differs from selection')
        cases, audit = [], []
        for identity, task in study.tasks.items():
            row = study.rows[identity]
            envelope = study.envelope(identity)
            result = envelope['result']
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
                        result['training'] != score['training'] or
                        result['prediction'] != score['prediction']):
                    raise ValueError('saved selected-task score differs')
                case['detail'] = selected_detail(
                    study.artifact(identity, 'epochs.json'), score)
            fit = (study.artifact(identity, 'fit.json') if
                   'artifacts/'+identity+'/fit.json' in envelope['artifacts'] else None)
            audit.append(fit_audit_row(case, fit))
            cases.append(case)
        rows = transfer_rows(cases)
        if (len(rows) != 4 or
                study.summary['charged']['native_calls'] > 3216):
            raise ValueError('four complete task groups and finite charges required')
        assessment = assess_transfer(rows, reference['reference_rms_m'])
        source = root/'analysis/lll/ilvis0_group_transfer_report.py'
        return dict(verified=True, study=STUDY,
                    manifest_sha256=MANIFEST_SHA256,
                    summary_sha256=study.completion['summary_sha256'],
                    reporter_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    qualification_request_sha256=digest(request),
                    qualification_tests_sha256=digest(tests),
                    tasks=16, passing_tasks=sum(case['passed'] for case in cases),
                    native_calls=study.summary['charged']['native_calls'],
                    selection=selection, reference=reference,
                    assessment=assessment, rows=rows, fit_audit=audit,
                    original_reads=0, protected_reads=0,
                    scientific_decision='abstain')
    finally:
        study.close()


def render(report):
    if (report.get('tasks') != 16 or len(report.get('selection', [])) != 4 or
            report.get('scientific_decision') != 'abstain'):
        raise ValueError('complete descriptive report required')
    assessment = report['assessment']
    rows = {row['segment_id']: row for row in report['rows']}
    scores = {row['segment_id']: row for row in assessment['group_rows']}
    lines = [
        '# Four-group forecast-error transfer', '',
        f"**{assessment['transfer_within_reference']}/4 groups** have second-cut "
        'north, east and height RMS errors within the fixed three-recording '
        'development reference.',
        f"{assessment['physical_screen_passed']}/4 pass the separate fixed physical "
        f"prediction screen; {assessment['abstentions']}/4 cannot be scored because "
        'the second-cut fit did not pass its numerical check.', '',
        '| Recording | IMU | Latitude | Duration | Second-cut result | Within reference | Physical screen |',
        '|---|---:|---:|---:|---|---|---|',
    ]
    for selected in report['selection']:
        segment = selected['segment_id']
        row = rows[segment]
        score = scores[segment]
        answer = lambda value: 'yes' if value is True else 'no' if value is False else '—'
        lines.append(
            f"| `{segment[:8]}…` | {selected['imu_type']} | "
            f"{float(selected['mean_latitude_deg']):.1f}° | "
            f"{float(selected['duration_s'])/60:.2f} min | {row['status']} | "
            f"{answer(score['transfer_within_reference'])} | "
            f"{answer(score['physical_screen_passed'])} |")
    lines += [
        '',
        'The reference is the maximum earlier forecast error from three prior',
        'development recordings under one declared clock and processing case.',
        'It is **not a confidence interval**. Four retrospective groups cannot',
        'establish a rare failure rate, calibrated Earth-model significance or',
        'the gyroscope channel’s separate contribution. A fit can remain a',
        'numerical failure even when another start looks promising. No result',
        'here changes the saved 53-stretch shape comparison.', '',
        '[Every group and direction](result.csv) · [All starts](fit-audit.csv) ·',
        '[Source selection](selection.csv) · [Fixed method](OBSERVED_PLAN.md) ·',
        '[Recovery procedure](RECOVERY.md)',
    ]
    return '\n'.join(lines)+'\n'


def publish(root='.'):
    from lll.ilvis0_rolling_origin_report import csv_bytes, audit_csv_bytes
    from lll.studies.artifacts import atomic, encoded
    root = Path(root).resolve()
    report = build(root)
    output = root/'docs/prediction-group-transfer'
    atomic(output/'RESULT.md', render(report).encode())
    atomic(output/'result.csv', csv_bytes(report))
    atomic(output/'fit-audit.csv', audit_csv_bytes(report))
    atomic(output/'verified-report.json', encoded(report))
    return report
