# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only accounting for generated bounded-solver forecast matrices."""

from collections import defaultdict

import numpy as np

from .ilvis0_solver_position import physical_metric


def summarize(cases,*,tasks,recipes,total_epochs,training_epochs,
              spread_limit_m,cost_range_limit):
    expected={task['identity']:task for task in tasks()}
    declared=recipes()
    if (not isinstance(cases,list) or len(cases)!=len(expected) or
            len({row['identity'] for row in cases})!=len(expected) or
            {row['identity'] for row in cases}!=set(expected)):
        raise ValueError('exact generated solver identities required')
    groups=defaultdict(list)
    for case in cases:
        task=expected[case['identity']]
        if any(case.get(key)!=value for key,value in task['payload'].items()):
            raise ValueError('frozen generated task label differs')
        groups[task['input_key']].append(case)
    fixtures=[]
    for key,r in declared.items():
        rows=groups[key]
        if len(rows)!=4:
            raise ValueError('four solver/start rows required per fixture')
        technical=sum(bool(row.get('technical_error')) for row in rows)
        stops=sum(row.get('converged') is True for row in rows)
        physical=sum(row.get('physical_accuracy_passed') is True
                     for row in rows)
        spread=cost_range=None
        if technical==0:
            paths=[np.asarray(row['forecast'],float) for row in rows]
            costs=np.asarray([row['training_cost'] for row in rows],float)
            if (any(path.shape!=(total_epochs,3) or
                    not np.all(np.isfinite(path)) for path in paths) or
                    not np.all(np.isfinite(costs))):
                raise ValueError('complete finite saved paths and costs required')
            metric=physical_metric(paths[0][training_epochs:])
            spread=max(float(np.max(np.linalg.norm(
                (a[training_epochs:]-b[training_epochs:])*metric,axis=1)))
                for index,a in enumerate(paths) for b in paths[index+1:])
            cost_range=float(np.max(costs)-np.min(costs))
        fixtures.append(dict(key=key,model=r['models'][0],clock=r['clock'],
            numerical_stops=stops,technical_failures=technical,
            physical_accuracy_passes=physical,
            maximum_later_path_spread_m=spread,
            maximum_training_cost_range=cost_range,
            passed=bool(technical==0 and stops==4 and
                        spread<=spread_limit_m and
                        cost_range<=cost_range_limit)))
    compact=[{key:case.get(key) for key in
        ('identity','model','sensor_case','solver','start','converged',
         'physical_accuracy_passed','training_cost',
         'prediction_horizontal_rms_m','prediction_vertical_rms_m',
         'evaluations','technical_error')} for case in cases]
    horizontal=[row['prediction_horizontal_rms_m'] for row in cases
                if row.get('prediction_horizontal_rms_m') is not None]
    vertical=[row['prediction_vertical_rms_m'] for row in cases
              if row.get('prediction_vertical_rms_m') is not None]
    passing=sum(row['passed'] for row in fixtures)
    return dict(tasks=len(expected),fixtures=len(fixtures),
        passing_fixtures=passing,passed=passing==len(fixtures),
        numerical_stops=sum(row.get('converged') is True for row in cases),
        physical_accuracy_passes=sum(row.get('physical_accuracy_passed') is True
                                     for row in cases),
        technical_failures=sum(bool(row.get('technical_error')) for row in cases),
        maximum_later_horizontal_rms_m=max(horizontal) if horizontal else None,
        maximum_later_height_rms_m=max(vertical) if vertical else None,
        fixture_rows=fixtures,task_rows=compact,
        scientific_decision='abstain',coverage_calibrated=False,
        observed_fit_starts=0)


def case_from_study(study,identity,task,*,total_epochs,training_epochs):
    """Read one sealed outcome, keeping technical failures visible."""
    outcome=study.envelope(identity)['result']
    case=dict(identity=identity,**task['payload'])
    names={name.rsplit('/',1)[-1]
           for name in study.envelope(identity)['artifacts']}
    if not {'fit.json','forecast.json'}<=names:
        case['technical_error']=outcome.get('reason','missing fit or forecast')
        return case
    fit=study.artifact(identity,'fit.json')
    forecast=study.artifact(identity,'forecast.json')
    if (outcome.get('technical_completion_only') is not True or
            outcome.get('forecast_saved_before_scoring') is not True or
            outcome.get('training_epochs')!=training_epochs or
            outcome.get('prediction_epochs')!=total_epochs-training_epochs or
            forecast.get('prediction_receiver_positions_used') is not False or
            fit['converged']!=outcome['converged'] or
            fit['residual_sum_squares']!=outcome['training_cost']):
        raise ValueError('sealed training/forecast record differs')
    case.update(converged=fit['converged'],
        physical_accuracy_passed=outcome['physical_accuracy_passed'],
        training_cost=outcome['training_cost'],
        prediction_horizontal_rms_m=outcome['prediction']['horizontal_rms_m'],
        prediction_vertical_rms_m=outcome['prediction']['vertical_rms_m'],
        forecast=forecast['coordinates'],evaluations=fit['evaluations'])
    return case


def build(root,*,study_id,tasks,recipes,total_epochs,training_epochs,
          spread_limit_m,cost_range_limit):
    from pathlib import Path
    from .studies.closed import ClosedStudy
    root=Path(root).resolve()
    study=ClosedStudy(root,'data/'+study_id)
    try:
        expected={task['identity']:task for task in tasks()}
        if (study.completion['state'] not in ('complete','terminal') or
                len(study.tasks)!=len(expected) or
                len(study.rows)!=len(expected) or
                study.manifest['limits']['maximum_identities']!=len(expected)):
            raise ValueError('exact sealed solver study required')
        if any(study.tasks[key]['payload']!=task['payload'] or
               study.tasks[key]['limits']!=task['limits']
               for key,task in expected.items()):
            raise ValueError('sealed solver tasks differ')
        declared=recipes()
        if {key:study.input(key) for key in declared}!=declared:
            raise ValueError('sealed solver recipes differ')
        cases=[]
        for identity,task in study.tasks.items():
            cases.append(case_from_study(study,identity,task,
                total_epochs=total_epochs,training_epochs=training_epochs))
        result=summarize(cases,tasks=tasks,recipes=recipes,
            total_epochs=total_epochs,training_epochs=training_epochs,
            spread_limit_m=spread_limit_m,
            cost_range_limit=cost_range_limit)
        result.update(study='data/'+study_id,
            manifest_sha256=study.completion['manifest_sha256'],
            summary_sha256=study.completion['summary_sha256'],
            charged=study.summary['charged'],original_reads=0,protected_reads=0)
        return result
    finally:study.close()
