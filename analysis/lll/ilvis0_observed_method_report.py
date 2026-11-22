# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only report for the three-recording optimizer development pilot."""

import csv
import hashlib
import io
from collections import Counter,defaultdict
from pathlib import Path

import numpy as np

from .ilvis0_observed_method_pilot import ID,ORIGINAL,SEGMENTS,tasks
from .ilvis0_solver_position import physical_metric

LIMIT_M=.1
COST_LIMIT=.01


def summarize(cases,layouts):
    expected={row['identity']:row for row in tasks(layouts)}
    if (len(cases)!=len(expected) or
            len({row['identity'] for row in cases})!=len(expected) or
            {row['identity'] for row in cases}!=set(expected)):
        raise ValueError('exact observed method identities required')
    groups=defaultdict(list)
    for case in cases:
        task=expected[case['identity']]
        if any(case.get(key)!=value for key,value in task['payload'].items()):
            raise ValueError('sealed observed task label differs')
        groups[(case['segment_id'],case['origin'])].append(case)
    cuts=[]
    for segment in SEGMENTS:
        for origin in ('inner','outer'):
            rows=groups[(segment,origin)]
            technical=sum(bool(row.get('technical_error')) for row in rows)
            stops=sum(row.get('converged') is True for row in rows)
            spread=cost_range=largest_path_pair=None
            if technical==0:
                cuts_seen={row['training_epochs'] for row in rows}
                horizons={row['prediction_epochs'] for row in rows}
                if len(cuts_seen)!=1 or len(horizons)!=1:
                    raise ValueError('one matched receiver cut required')
                cut=cuts_seen.pop();horizon=horizons.pop()
                paths=[np.asarray(row['forecast'],float) for row in rows]
                costs=np.asarray([row['training_cost'] for row in rows],float)
                if (any(path.shape!=(cut+horizon,3) or
                        not np.all(np.isfinite(path)) for path in paths) or
                        not np.all(np.isfinite(costs))):
                    raise ValueError('complete finite observed paths and costs required')
                metric=physical_metric(paths[0][cut:])
                pair_spreads=[(float(np.max(np.linalg.norm(
                    (a[cut:]-b[cut:])*metric,axis=1))),
                    rows[index]['identity'],rows[other]['identity'])
                    for index,a in enumerate(paths)
                    for other,b in enumerate(paths) if other>index]
                spread,first,second=max(pair_spreads)
                largest_path_pair=[first,second]
                cost_range=float(np.ptp(costs))
            cuts.append(dict(segment_id=segment,origin=origin,
                numerical_stops=stops,technical_failures=technical,
                maximum_later_path_spread_m=spread,
                largest_path_pair=largest_path_pair,
                training_cost_range=cost_range,
                within_diagnostic_scales=bool(technical==0 and
                    spread<=LIMIT_M and cost_range<=COST_LIMIT)))
    return dict(version='ilvis0-observed-method-report-v1',
        tasks=len(expected),cuts=len(cuts),
        technical_failures=sum(bool(row.get('technical_error')) for row in cases),
        numerical_stops=sum(row.get('converged') is True for row in cases),
        numerical_stops_by_solver={solver:sum(
            row['solver']==solver and row.get('converged') is True
            for row in cases) for solver in ('trust_v2','scipy_trf')},
        nonstopping_reasons=dict(sorted(Counter(
            row.get('probe_reason') or 'unclassified'
            for row in cases if row.get('converged') is False
            and not row.get('technical_error')).items())),
        method_agreement_within_diagnostic_scale=sum(
            row['within_diagnostic_scales'] for row in cuts),
        cut_rows=cuts,task_rows=[{key:row.get(key) for key in
            ('identity','segment_id','origin','solver','start','converged',
             'evaluations','termination','message','stopping_rule_verified',
             'stability_verified','probe_reason','fresh_stationarity',
             'probe_actual_cost_change','probe_parameter_step',
             'position_probe_rms_m','position_probe_max_m','training_cost',
             'prediction_north_rms_m','prediction_east_rms_m',
             'prediction_horizontal_rms_m',
             'prediction_vertical_rms_m','active_bounds',
             'parameters','technical_error')} for row in cases],
        observed_fit_starts=len(expected),original_reclassified=0,
        scientific_decision='abstain',coverage_calibrated=False)


def select_completed(studies,expected):
    """Reuse each sealed fit once across an original and finite recovery."""
    selected={}
    for study in studies:
        for identity,row in study.rows.items():
            if (identity not in expected or
                    study.tasks[identity]['payload']!=expected[identity]['payload']):
                raise ValueError('sealed observed method task differs')
            if row['status']=='complete':
                if identity in selected:
                    raise ValueError('duplicate completed observed fit')
                selected[identity]=study
    if set(selected)!=set(expected):
        raise ValueError('all observed method identities must complete')
    return selected


def build(root='.',*,study_id=ID,recovery=None):
    from .studies.closed import ClosedStudy
    from .studies.task_resume import resume_campaign
    root=Path(root).resolve()
    recovery_state=None
    if recovery is not None:
        recovery_state=resume_campaign(root,root/recovery,launch=False)
        if recovery_state['state']!='all_tasks_finished':
            raise ValueError('complete verified observed recovery required')
    study=ClosedStudy(root,'data/'+study_id)
    prior=ClosedStudy(root,ORIGINAL)
    stages=[]
    try:
        if recovery_state is not None:
            for index in range(recovery_state['stages']):
                stages.append(ClosedStudy(root,recovery+f'/stage-{index:03d}'))
        layouts=study.input('layouts')
        if (study.completion['state'] not in ('complete','terminal') or
                len(study.tasks)!=24 or
                (recovery_state is None and len(study.rows)!=24) or
                study.manifest['limits']['maximum_identities']!=24 or
                len(prior.tasks)!=80 or len(prior.rows)!=80 or
                study.input('original_completion')!=prior.completion):
            raise ValueError('exact sealed observed method and prior studies required')
        if layouts!=[next(row for row in prior.input('layouts')
                          if row['segment_id']==segment) for segment in SEGMENTS]:
            raise ValueError('sealed selected receiver layouts differ')
        selected={row['segment_id']:row for row in csv.DictReader(
            io.StringIO(study.input('selection',raw=True).decode()))}
        if any(segment not in selected for segment in SEGMENTS):
            raise ValueError('sealed three-recording metadata differs')
        expected={row['identity']:row for row in tasks(layouts)}
        completed=select_completed([study,*stages],expected)
        cases=[]
        for identity,task in expected.items():
            source=completed[identity]
            task=source.tasks[identity]
            if task['payload']!=expected[identity]['payload']:
                raise ValueError('sealed observed method task differs')
            outcome=source.envelope(identity)['result']
            case=dict(identity=identity,**task['payload'])
            names={name.rsplit('/',1)[-1]
                   for name in source.envelope(identity)['artifacts']}
            if not {'fit.json','forecast.json','scores.json'}<=names:
                case['technical_error']=outcome.get('reason','missing fit/forecast')
            else:
                fit=source.artifact(identity,'fit.json')
                forecast=source.artifact(identity,'forecast.json')
                scores=source.artifact(identity,'scores.json')
                if (outcome.get('technical_completion_only') is not True or
                        fit['converged']!=outcome['converged'] or
                        fit['residual_sum_squares']!=outcome['training_cost'] or
                        forecast['prediction_receiver_positions_used'] is not False or
                        forecast['continuous_propagation_without_gps_reset'] is not True or
                        scores['prediction']!=outcome['prediction']):
                    raise ValueError('sealed observed forecast evidence differs')
                probe=fit.get('stability_probe') or {}
                case.update(converged=fit['converged'],
                    evaluations=fit['evaluations'],
                    termination=fit.get('termination'),
                    message=fit.get('message'),
                    stopping_rule_verified=fit.get('stopping_rule_verified'),
                    stability_verified=fit.get('stability_verified'),
                    probe_reason=probe.get('reason'),
                    fresh_stationarity=probe.get('fresh_stationarity'),
                    probe_actual_cost_change=probe.get('actual_cost_change'),
                    probe_parameter_step=probe.get('normalized_parameter_step'),
                    position_probe_rms_m=probe.get('position_rms_neu_m'),
                    position_probe_max_m=probe.get('position_max_abs_neu_m'),
                    training_cost=fit['residual_sum_squares'],
                    parameters=fit['parameters'],
                    active_bounds=fit['active_bounds'],
                    prediction_north_rms_m=outcome['prediction']['north_rms_m'],
                    prediction_east_rms_m=outcome['prediction']['east_rms_m'],
                    prediction_horizontal_rms_m=outcome['prediction']['horizontal_rms_m'],
                    prediction_vertical_rms_m=outcome['prediction']['vertical_rms_m'],
                    training_epochs=forecast['training_epochs'],
                    prediction_epochs=forecast['prediction_epochs'],
                    forecast=forecast['coordinates'])
            cases.append(case)
        report=summarize(cases,layouts)
        original_converged=0;comparisons=[]
        for case in cases:
            if case['solver']!='trust_v2' or 'forecast' not in case:
                continue
            identity=(f"{case['segment_id']}-{case['origin']}-0-"
                      f"header_elapsed-{case['start']}")
            original_fit=prior.artifact(identity,'fit.json')
            original_forecast=prior.artifact(identity,'forecast.json')
            original_converged+=original_fit['converged'] is True
            original_path=np.asarray(original_forecast['coordinates'],float)
            new_path=np.asarray(case['forecast'],float)
            cut=case['training_epochs']
            if (original_path.shape!=new_path.shape or
                    original_forecast['training_epochs']!=cut):
                raise ValueError('original and new receiver cuts differ')
            delta=(new_path[cut:]-original_path[cut:])*physical_metric(original_path[cut:])
            comparisons.append(float(np.max(np.linalg.norm(delta,axis=1))))
        report.update(study='data/'+study_id,original_study=ORIGINAL,
            selected_recordings=[{key:selected[segment][key] for key in
                ('segment_id','filename','start_utc','duration_s',
                 'mean_latitude_deg','median_ground_speed_kmh')}
                 for segment in SEGMENTS],
            original_matched_starts=len(comparisons),
            original_converged_in_matched_starts=original_converged,
            maximum_new_trust_vs_original_path_spread_m=
                max(comparisons) if comparisons else None,
            manifest_sha256=study.completion['manifest_sha256'],
            summary_sha256=study.completion['summary_sha256'],
            original_manifest_sha256=prior.completion['manifest_sha256'],
            original_summary_sha256=prior.completion['summary_sha256'],
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            charged={key:sum(item.summary['charged'][key]
                             for item in [study,*stages])
                     for key in study.summary['charged']})
        if recovery_state is not None:
            report.update(recovery=recovery,
                technical_interruptions=recovery_state['technical_interruptions'],
                stage_manifest_sha256=[item.completion['manifest_sha256']
                                       for item in stages])
        return report
    finally:
        for item in stages:item.close()
        prior.close();study.close()


def render(report,*,plan='OBSERVED_METHOD_PILOT_PLAN.md',
           task_file='observed-method-tasks.csv'):
    lines=['# Observed optimizer comparison','',
        f"{report['tasks']}/24 planned recorded-data fits were preserved. "
        f"{report['numerical_stops']}/24 passed their new numerical stopping "
        f"checks; {report['technical_failures']} had technical errors. "
        f"{report['method_agreement_within_diagnostic_scale']}/6 matched "
        'recording/cut sets met the declared development agreement scales. '
        f"Stops by method: custom trust-region "
        f"{report['numerical_stops_by_solver']['trust_v2']}/12; SciPy TRF "
        f"{report['numerical_stops_by_solver']['scipy_trf']}/12.",'',
        '| Recording ID | Cut | Stops | Largest later-path spread | Training cost range |',
        '|---|---|---:|---:|---:|']
    for row in report['cut_rows']:
        spread=row['maximum_later_path_spread_m']
        cost=row['training_cost_range']
        lines.append(f"| {row['segment_id']} | {row['origin']} | "
            f"{row['numerical_stops']}/4 | "
            f"{'—' if spread is None else f'{spread:.3g} m'} | "
            f"{'—' if cost is None else f'{cost:.3g}'} |")
    reasons=report.get('nonstopping_reasons',{})
    if reasons:
        readable={'fresh_position_probe_not_stable':'fresh position stability',
                  'not_stationary':'fresh stationarity'}
        detail=', '.join(f"{count} failed {readable.get(key,key)}"
                         for key,count in reasons.items())
        lines += ['',f'The {sum(reasons.values())} nonstopping fits: {detail}. '
                  'These are numerical stopping outcomes, not evidence for '
                  'or against an Earth model.']
    lines += ['',
        'The three selected development stretches span a northern and two '
        'southern routes. Their source, duration, latitude and speed are '
        'preserved in the saved report and original selection ledger.']
    selected=report.get('selected_recordings',[])
    if selected:
        lines += ['', '| Recording | Duration | Mean latitude | Ground speed |',
                  '|---|---:|---:|---:|']
        for row in selected:
            lines.append(f"| {Path(row['filename']).name} | "
                f"{float(row['duration_s'])/60:.1f} min | "
                f"{float(row['mean_latitude_deg']):.1f}° | "
                f"{float(row['median_ground_speed_kmh']):.0f} km/h |")
    lines += ['',
        'The two methods fit identical earlier receiver observations to the '
        'recorded IMU increments. Later receiver positions were opened only '
        'after each continuous forecast was saved. This is a numerical method '
        'diagnostic for one specified-field globe candidate, not a globe/flat '
        'comparison or a calibrated aircraft detection. A 0.1 m path spread '
        'and 0.01 cost range are development scales, not acceptance thresholds. '
        f"The original 80-fit study and its 50 nonpassing labels remain intact; "
        f"{report['original_matched_starts']} sealed original starts were "
        'compared without reclassification.','',
        f'[All new fit outcomes]({task_file}) · '
        f'[Frozen plan]({plan}) · '
        '[Source selection](remaining-groups.csv) · '
        '[Why the method did not qualify](OBSERVED_METHOD_V2_DIAGNOSIS.md)']
    return '\n'.join(lines)+'\n'


def csv_bytes(report):
    base=('identity','segment_id','origin','solver','start','converged',
            'evaluations','termination','message','stopping_rule_verified',
            'stability_verified','probe_reason','fresh_stationarity',
            'probe_actual_cost_change','probe_parameter_step',
            'position_probe_rms_m','position_probe_max_m','training_cost',
            'prediction_north_rms_m','prediction_east_rms_m',
            'prediction_horizontal_rms_m',
            'prediction_vertical_rms_m','active_bounds','technical_error')
    parameters=sorted({key for row in report['task_rows']
                       for key in (row.get('parameters') or {})})
    fields=(*base,*(f'calibration_{key}' for key in parameters))
    stream=io.StringIO(newline='')
    writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n')
    writer.writeheader()
    for row in report['task_rows']:
        data={field:row.get(field) for field in base}
        data['active_bounds']=';'.join(row.get('active_bounds') or ())
        data.update({f'calibration_{key}':(row.get('parameters') or {}).get(key)
                     for key in parameters})
        writer.writerow(data)
    return stream.getvalue().encode()


def publish(root='.'):
    from .studies.artifacts import atomic,encoded
    root=Path(root).resolve();report=build(root)
    output=root/'docs/prediction-group-transfer'
    atomic(output/'OBSERVED_METHOD_PILOT_RESULT.md',render(report).encode())
    atomic(output/'observed-method-tasks.csv',csv_bytes(report))
    atomic(output/'observed-method-report.json',encoded(report))
    return report


if __name__=='__main__':
    result=publish()
    print('cuts within diagnostic scale:',
          result['method_agreement_within_diagnostic_scale'],'/',result['cuts'])
