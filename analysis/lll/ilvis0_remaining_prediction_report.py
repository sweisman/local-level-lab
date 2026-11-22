# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only accounting for the twenty-group NASA forecast extension."""

import math
import csv
import hashlib
import io
from pathlib import Path

from .ilvis0_remaining_prediction_study import SCOPE

AXES=('north','east','vertical')
STUDY='data/ilvis0-remaining-prediction-transfer-20261118'
MANIFEST_SHA256='3cc9a72f3c3f3fa10c3f867fe31443fecfb7ee320dcb3567692d0af678c2863e'
SELECTION='docs/prediction-group-transfer/remaining-groups.csv'
QUALIFICATION='docs/prediction-group-transfer/remaining-report-qualification-request.json'
REQUIRED_TESTS=(
    'test_all_twenty_selected_groups_remain_in_denominator',
    'test_missing_or_duplicate_group_cannot_inflate_transfer_count',
    'test_physical_screen_is_separate_from_relative_reference',
    'test_public_summary_keeps_scope_and_abstentions_visible',
    'test_saved_builder_requires_exact_closed_eighty_task_study',
    'test_group_csv_joins_frozen_metadata_and_scores',
    'test_publication_requires_source_bound_qualification',
)


def qualification_sources(root):
    from .studies.dependencies import source_closure
    return source_closure(root,[
        'analysis/lll/ilvis0_remaining_prediction_report.py',
        'analysis/tests/test_ilvis0_remaining_prediction_report.py'])


def verify_closed(study):
    if (study.completion['state'] not in ('complete','terminal') or
            study.completion['manifest_sha256']!=MANIFEST_SHA256 or
            len(study.tasks)!=80 or len(study.rows)!=80 or
            study.manifest['allocation']['total']!=4 or
            study.manifest['limits']['maximum_identities']!=80 or
            study.manifest['limits']['native_calls']!=16080 or
            study.manifest['scope']!=SCOPE):
        raise ValueError('exact closed eighty-task prediction study required')


def assess(rows,reference):
    if (not isinstance(rows,list) or len(rows)!=20 or
            not isinstance(reference,dict) or set(reference)!=set(AXES) or
            any(not isinstance(reference[axis],(int,float)) or
                    not math.isfinite(reference[axis]) or reference[axis]<=0
                    for axis in AXES)):
        raise ValueError('twenty groups and finite positive reference required')
    seen=set()
    group_rows=[]
    for row in rows:
        segment=row.get('segment_id') if isinstance(row,dict) else None
        status=row.get('status') if isinstance(row,dict) else None
        if (not isinstance(segment,str) or not segment or segment in seen or
                status not in ('matched','abstain_inner','abstain_outer',
                               'abstain_both')):
            raise ValueError('unique group and valid stopping status required')
        seen.add(segment)
        if status in ('abstain_outer','abstain_both'):
            group_rows.append(dict(segment_id=segment,status=status,
                transfer_within_reference=None,physical_screen_passed=None))
            continue
        names=[axis+'_outer_rms_m' for axis in AXES]
        names+=['outer_maximum_horizontal_m','outer_maximum_absolute_up_m']
        values=[row.get(name) for name in names]
        if any(not isinstance(v,(int,float)) or not math.isfinite(v) or v<0
               for v in values):
            raise ValueError('complete finite second-cut score required')
        north,east,up,max_horizontal,max_up=values
        within=all(row[axis+'_outer_rms_m']<=reference[axis] for axis in AXES)
        physical=(math.hypot(north,east)<=10. and up<=30. and
                  max_horizontal<=50. and max_up<=150.)
        group_rows.append(dict(segment_id=segment,status=status,
            transfer_within_reference=within,physical_screen_passed=physical,
            rms_to_reference={axis:row[axis+'_outer_rms_m']/reference[axis]
                              for axis in AXES}))
    return dict(version='ilvis0-twenty-group-prediction-assessment-v1',
        groups=20,abstentions=sum(row['transfer_within_reference'] is None
                                 for row in group_rows),
        transfer_within_reference=sum(row['transfer_within_reference'] is True
                                      for row in group_rows),
        physical_screen_passed=sum(row['physical_screen_passed'] is True
                                   for row in group_rows),
        group_rows=group_rows,reference_rms_m=dict(reference),
        reference_is_confidence_limit=False,coverage_calibrated=False,
        scientific_decision='abstain')


def render(report):
    selection=report.get('selection',[])
    rows=report.get('rows',[])
    assessment=report.get('assessment',{})
    if (len(selection)!=20 or len(rows)!=20 or
            assessment.get('groups')!=20 or
            assessment.get('scientific_decision')!='abstain'):
        raise ValueError('complete twenty-group descriptive report required')
    by_id={row['segment_id']:row for row in rows}
    judged={row['segment_id']:row for row in assessment['group_rows']}
    if (len(by_id)!=20 or len(judged)!=20 or
            set(by_id)!={row['segment_id'] for row in selection} or
            set(judged)!=set(by_id)):
        raise ValueError('twenty selected groups must match saved scores')
    answer=lambda value:'yes' if value is True else 'no' if value is False else '—'
    lines=['# Forecasts across twenty more airborne recording groups','',
        f"**{assessment['transfer_within_reference']}/20** groups have later "
        'north, east and height errors within the fixed earlier development reference.',
        f"**{assessment['physical_screen_passed']}/20** pass the separate "
        f"physical prediction screen; {assessment['abstentions']}/20 cannot "
        'be scored because the later-cut fit did not pass its numerical check.','',
        '| Recording | IMU | Latitude | Duration | Numerical status | Within reference | Physical screen |',
        '|---|---:|---:|---:|---|---|---|']
    for selected in selection:
        segment=selected['segment_id']
        row=by_id[segment]
        score=judged[segment]
        lines.append(f"| `{segment[:8]}…` | {selected['imu_type']} | "
                     f"{float(selected['mean_latitude_deg']):.1f}° | "
                     f"{float(selected['duration_s'])/60:.2f} min | "
                     f"{row['status']} | {answer(score['transfer_within_reference'])} | "
                     f"{answer(score['physical_screen_passed'])} |")
    lines += ['',
        'These groups were selected without looking at the forecast outcomes,',
        'but they come from the same archive: this is retrospective development,',
        'not independent confirmation. The reference is a fixed earlier error',
        'comparison, not a confidence interval. This study checks one specified',
        'globe-plus-field forecast; it does not compare Earth shapes or calibrate',
        'a detection rule. Overlapping survey flights or installations cannot be',
        'counted as independent replications.','',
        '[Group metadata and forecast errors](remaining-group-summary.csv) · '
        '[Detailed forecast errors](remaining-result.csv) · '
        '[All numerical starts](remaining-fit-audit.csv) · '
        '[Source selection](remaining-groups.csv) · '
        '[Frozen method](REMAINING_GROUPS_PREDICTION_PLAN.md) · '
        '[Recovery procedure](REMAINING_GROUPS_RECOVERY.md)']
    return '\n'.join(lines)+'\n'


def group_csv(report):
    fields=['group_id','segment_id','filename','start_utc','end_utc',
            'duration_s','imu_type','mean_latitude_deg','mean_course_deg',
            'minimum_ground_speed_kmh','median_ground_speed_kmh',
            'status','inner_identity','outer_identity',
            'north_inner_rms_m','east_inner_rms_m','vertical_inner_rms_m',
            'north_outer_rms_m','east_outer_rms_m','vertical_outer_rms_m',
            'outer_maximum_horizontal_m','outer_maximum_absolute_up_m',
            'transfer_within_reference','physical_screen_passed']
    selection=report['selection']
    rows={row['segment_id']:row for row in report['rows']}
    assessment={row['segment_id']:row for row in report['assessment']['group_rows']}
    if (len(selection)!=20 or len(rows)!=20 or len(assessment)!=20 or
            {row['segment_id'] for row in selection}!=set(rows) or
            set(assessment)!=set(rows)):
        raise ValueError('twenty matched group rows required')
    stream=io.StringIO(newline='')
    writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n')
    writer.writeheader()
    for chosen in selection:
        segment=chosen['segment_id']
        combined=dict(chosen)
        combined.update(rows[segment])
        combined.update(assessment[segment])
        writer.writerow({field:combined.get(field) for field in fields})
    return stream.getvalue().encode()


def build(root='.'):
    """Replay every sealed task; never open originals or refit a model."""
    from .ilvis0_rolling_origin_report import (
        fit_audit_row,selected_detail,transfer_rows)
    from .prediction_transfer_reference import from_saved_csv
    from .studies.artifacts import digest
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .ilvis0_control_shards import runtime_environment

    root=Path(root).resolve()
    request,tests=checked(root,QUALIFICATION,
        sources=qualification_sources(root),environment=runtime_environment(),
        required_tests=REQUIRED_TESTS,minimum_tests=len(REQUIRED_TESTS))
    study=ClosedStudy(root,STUDY)
    try:
        verify_closed(study)
        reference=from_saved_csv(
            (root/'docs/prediction-rolling-origin/result.csv').read_bytes(),
            expected_sha256='651ae7c87d28d4d5e2d4b9493d3f5a990fc550adc1972c30d970e3bc32ac4117')
        if study.input('transfer-reference')!=reference:
            raise ValueError('frozen development reference differs')
        selection_raw=(root/SELECTION).read_bytes()
        receipt=study.input('selection-receipt')
        if digest(selection_raw)!=receipt['selection_sha256']:
            raise ValueError('frozen twenty-group selection differs')
        selection=list(csv.DictReader(io.StringIO(selection_raw.decode())))
        layouts=study.input('layouts')
        if (len(selection)!=20 or len(layouts)!=20 or
                [row['segment_id'] for row in selection]!=
                [row['segment_id'] for row in layouts]):
            raise ValueError('frozen group order differs')
        cases=[]
        audit=[]
        for identity,task in study.tasks.items():
            row=study.rows[identity]
            envelope=study.envelope(identity)
            result=envelope['result']
            payload=task['payload']
            case=dict(identity=identity,segment_id=payload['segment_id'],
                origin=payload['origin'],profile=payload['profile'],
                clock=payload['clock'],start=payload['start'],
                passed=row['passed'],training_cost=result.get('training_cost'),
                prediction=result.get('prediction'))
            if row['passed']:
                score=study.artifact(identity,'scores.json')
                if (result['scientific_decision']!='abstain' or
                        result['training']!=score['training'] or
                        result['prediction']!=score['prediction']):
                    raise ValueError('sealed selected-task score differs')
                case['detail']=selected_detail(study.artifact(identity,'epochs.json'),score)
            fit=(study.artifact(identity,'fit.json') if
                 'artifacts/'+identity+'/fit.json' in envelope['artifacts'] else None)
            audit.append(fit_audit_row(case,fit))
            cases.append(case)
        rows=transfer_rows(cases)
        if (len(rows)!=20 or {row['segment_id'] for row in rows}!=
                {row['segment_id'] for row in selection} or
                study.summary['charged']['native_calls']>16080):
            raise ValueError('complete finite twenty-group evidence required')
        assessment=assess(rows,reference['reference_rms_m'])
        return dict(version='ilvis0-twenty-group-prediction-report-v1',
            verified=True,study=STUDY,manifest_sha256=MANIFEST_SHA256,
            summary_sha256=study.completion['summary_sha256'],
            reporter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            qualification_request_sha256=digest(request),
            qualification_tests_sha256=digest(tests),
            tasks=80,passing_tasks=sum(case['passed'] for case in cases),
            native_calls=study.summary['charged']['native_calls'],
            selection=selection,reference=reference,assessment=assessment,
            rows=rows,fit_audit=audit,original_reads=0,protected_reads=0,
            scientific_decision='abstain')
    finally:
        study.close()


def publish(root='.'):
    from .ilvis0_rolling_origin_report import csv_bytes,audit_csv_bytes
    from .studies.artifacts import atomic,encoded
    root=Path(root).resolve()
    report=build(root)
    output=root/'docs/prediction-group-transfer'
    atomic(output/'REMAINING_GROUPS_PREDICTION_RESULT.md',render(report).encode())
    atomic(output/'remaining-group-summary.csv',group_csv(report))
    atomic(output/'remaining-result.csv',csv_bytes(report))
    atomic(output/'remaining-fit-audit.csv',audit_csv_bytes(report))
    atomic(output/'remaining-verified-report.json',encoded(report))
    return report


if __name__=='__main__':
    result=publish()
    print(dict(groups=result['assessment']['groups'],
               passing_tasks=result['passing_tasks'],
               within_reference=result['assessment']['transfer_within_reference'],
               physical_screen=result['assessment']['physical_screen_passed'],
               abstentions=result['assessment']['abstentions']))
