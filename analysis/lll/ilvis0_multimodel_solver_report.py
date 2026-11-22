# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only accounting for six full-calibration generated fixtures."""

import csv
import hashlib
import io
from pathlib import Path

import numpy as np

from .ilvis0_multimodel_solver_study import ID,MODELS,SENSOR_CASES,tasks
from .ilvis0_solver_position import physical_metric


def summarize(cases):
    expected={task['identity']:task for task in tasks()}
    if (not isinstance(cases,list) or len(cases)!=24 or
            len({case['identity'] for case in cases})!=24 or
            {case['identity'] for case in cases}!=set(expected)):
        raise ValueError('exact 24 generated multimodel identities required')
    groups={}
    for case in cases:
        task=expected[case['identity']]
        if any(case.get(key)!=value for key,value in task['payload'].items()):
            raise ValueError('frozen generated task label differs')
        groups.setdefault((case['model'],case['sensor_case']),[]).append(case)
    fixtures=[]
    for model in MODELS:
        for sensor in SENSOR_CASES:
            rows=groups[(model,sensor)]
            technical=sum(bool(row.get('technical_error')) for row in rows)
            stops=sum(row.get('converged') is True for row in rows)
            physical=sum(row.get('physical_accuracy_passed') is True
                         for row in rows)
            spread=None
            if technical==0:
                paths=[np.asarray(row['forecast'],float) for row in rows]
                if any(path.shape!=(59,3) or not np.all(np.isfinite(path))
                       for path in paths):
                    raise ValueError('complete finite saved paths required')
                metric=physical_metric(paths[0][39:])
                spread=max(float(np.max(np.linalg.norm(
                    (a[39:]-b[39:])*metric,axis=1)))
                    for index,a in enumerate(paths) for b in paths[index+1:])
            fixtures.append(dict(model=model,sensor_case=sensor,
                technical_failures=technical,numerical_stops=stops,
                physical_accuracy_passes=physical,
                maximum_later_path_spread_m=spread,
                passed=bool(technical==0 and stops==4 and spread<=.1)))
    compact=[{key:case.get(key) for key in
        ('identity','model','sensor_case','solver','start','converged',
         'physical_accuracy_passed','training_cost',
         'prediction_horizontal_rms_m','prediction_vertical_rms_m',
         'evaluations','technical_error')} for case in cases]
    passing=sum(row['passed'] for row in fixtures)
    horizontal=[row['prediction_horizontal_rms_m'] for row in cases
                if row.get('prediction_horizontal_rms_m') is not None]
    vertical=[row['prediction_vertical_rms_m'] for row in cases
              if row.get('prediction_vertical_rms_m') is not None]
    return dict(version='ilvis0-multimodel-solver-report-v1',
        tasks=24,fixtures=6,passing_fixtures=passing,passed=passing==6,
        numerical_stops=sum(row.get('converged') is True for row in cases),
        physical_accuracy_passes=sum(row.get('physical_accuracy_passed') is True
                                     for row in cases),
        technical_failures=sum(bool(row.get('technical_error')) for row in cases),
        maximum_later_horizontal_rms_m=max(horizontal) if horizontal else None,
        maximum_later_height_rms_m=max(vertical) if vertical else None,
        fixture_rows=fixtures,task_rows=compact,
        scientific_decision='abstain',coverage_calibrated=False,
        observed_fit_starts=0)


def build(root='.'):
    from .studies.closed import ClosedStudy
    root=Path(root).resolve()
    study=ClosedStudy(root,'data/'+ID)
    try:
        if (study.completion['state'] not in ('complete','terminal') or
                len(study.tasks)!=24 or len(study.rows)!=24 or
                study.manifest['limits']['maximum_identities']!=24):
            raise ValueError('exact sealed multimodel generated study required')
        cases=[]
        for identity,task in study.tasks.items():
            outcome=study.envelope(identity)['result']
            case=dict(identity=identity,**task['payload'])
            names={name.rsplit('/',1)[-1]
                   for name in study.envelope(identity)['artifacts']}
            if not {'fit.json','forecast.json'}<=names:
                case['technical_error']=outcome.get('reason','missing fit or forecast')
            else:
                fit=study.artifact(identity,'fit.json')
                forecast=study.artifact(identity,'forecast.json')
                if (outcome.get('technical_completion_only') is not True or
                        outcome.get('forecast_saved_before_scoring') is not True or
                        outcome.get('training_epochs')!=39 or
                        outcome.get('prediction_epochs')!=20 or
                        forecast.get('prediction_receiver_positions_used') is not False or
                        fit['converged']!=outcome['converged'] or
                        fit['residual_sum_squares']!=outcome['training_cost']):
                    raise ValueError('sealed generated fit/forecast record differs')
                case.update(converged=fit['converged'],
                    physical_accuracy_passed=outcome['physical_accuracy_passed'],
                    training_cost=outcome['training_cost'],
                    prediction_horizontal_rms_m=outcome['prediction']['horizontal_rms_m'],
                    prediction_vertical_rms_m=outcome['prediction']['vertical_rms_m'],
                    forecast=forecast['coordinates'],evaluations=fit['evaluations'])
            cases.append(case)
        report=summarize(cases)
        report.update(study='data/'+ID,
            manifest_sha256=study.completion['manifest_sha256'],
            summary_sha256=study.completion['summary_sha256'],
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            charged=study.summary['charged'],original_reads=0,protected_reads=0)
        return report
    finally:study.close()


def render(report):
    lines=['# Multimodel generated solver forecast check','',
        f"**{report['passing_fixtures']}/6** generated fixtures pass the "
        'four-fit numerical/forecast-agreement gate. '
        f"{report['numerical_stops']}/24 fits passed numerical stopping; "
        f"{report['physical_accuracy_passes']}/24 passed the separate "
        f"generated physical screen; {report['technical_failures']} had "
        'technical failures.','',
        '| Generated model | Calibration | Numerical stops | Physical screen | Largest later-path spread |',
        '|---|---|---:|---:|---:|']
    for row in report['fixture_rows']:
        spread=row['maximum_later_path_spread_m']
        lines.append(f"| {row['model']} | {row['sensor_case']} | "
            f"{row['numerical_stops']}/4 | {row['physical_accuracy_passes']}/4 | "
            f"{spread:.3g} m |" if spread is not None else
            f"| {row['model']} | {row['sensor_case']} | "
            f"{row['numerical_stops']}/4 | {row['physical_accuracy_passes']}/4 | — |")
    horizontal=report['maximum_later_horizontal_rms_m']
    vertical=report['maximum_later_height_rms_m']
    if horizontal is not None and vertical is not None:
        lines += ['',
            f'Largest later RMS error against generated truth: '
            f'{horizontal:.3g} m horizontal and {vertical:.3g} m in height.']
    lines += ['',
        'These are software controls generated outside the fitter. The six '
        'model/calibration fixtures share one declared noise seed, so they '
        'are not six independent statistical replications. '
        'Each fit sees only 39 earlier receiver reports and predicts 20 later '
        'reports. Solver agreement and generated physical accuracy are '
        'separate outcomes. This does not revise any aircraft fit, calibrate '
        'prediction coverage or open reserved confirmation flights.','',
        '[Frozen plan](MULTIMODEL_SOLVER_PLAN.md) · '
        '[All fit outcomes](multimodel-solver-tasks.csv)']
    return '\n'.join(lines)+'\n'


def task_csv(report):
    fields=('identity','model','sensor_case','solver','start','converged',
            'physical_accuracy_passed','training_cost',
            'prediction_horizontal_rms_m','prediction_vertical_rms_m',
            'evaluations','technical_error')
    stream=io.StringIO(newline='')
    writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n')
    writer.writeheader()
    for row in report['task_rows']:
        writer.writerow({key:row.get(key) for key in fields})
    return stream.getvalue().encode()


def publish(root='.'):
    from .studies.artifacts import atomic,encoded
    root=Path(root).resolve()
    report=build(root)
    output=root/'docs/prediction-group-transfer'
    atomic(output/'MULTIMODEL_SOLVER_RESULT.md',render(report).encode())
    atomic(output/'multimodel-solver-tasks.csv',task_csv(report))
    atomic(output/'multimodel-solver-report.json',encoded(report))
    return report


if __name__=='__main__':
    report=publish()
    print('fixtures:',report['passing_fixtures'],'/',report['fixtures'])
