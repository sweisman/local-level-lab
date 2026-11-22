# SPDX-License-Identifier: AGPL-3.0-or-later
"""Hash-checked saved-only report for the exact-grid nominal-clock control."""

import hashlib
from pathlib import Path

from .ilvis0_multimodel_solver_report import summarize as shared_summarize
from .ilvis0_multimodel_solver_report import task_csv
from .ilvis0_nominal_solver_study import ID,recipes,tasks


def summarize(cases):
    result=shared_summarize(cases)
    result['version']='ilvis0-nominal-200hz-solver-report-v1'
    return result


def build(root='.'):
    from .studies.closed import ClosedStudy
    root=Path(root).resolve()
    study=ClosedStudy(root,'data/'+ID)
    try:
        if (study.completion['state'] not in ('complete','terminal') or
                len(study.tasks)!=24 or len(study.rows)!=24 or
                study.manifest['limits']['maximum_identities']!=24):
            raise ValueError('exact sealed 24-task nominal study required')
        expected={task['identity']:task for task in tasks()}
        if any(study.tasks[key]['payload']!=task['payload'] or
               study.tasks[key]['limits']!=task['limits']
               for key,task in expected.items()):
            raise ValueError('sealed nominal task definitions differ')
        declared=recipes()
        saved={key:study.input(key) for key in declared}
        if saved!=declared or any(r['rate_hz']!=200 or
                r['clock']!='nominal_200Hz' for r in saved.values()):
            raise ValueError('sealed nominal recipes differ')
        seeds=[r['noise_by_law']['increment']['seed'] for r in saved.values()]
        if len(set(seeds))!=6:
            raise ValueError('six distinct generated noise seeds required')
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
                    raise ValueError('sealed nominal fit/forecast record differs')
                case.update(converged=fit['converged'],
                    physical_accuracy_passed=outcome['physical_accuracy_passed'],
                    training_cost=outcome['training_cost'],
                    prediction_horizontal_rms_m=outcome['prediction']['horizontal_rms_m'],
                    prediction_vertical_rms_m=outcome['prediction']['vertical_rms_m'],
                    forecast=forecast['coordinates'],evaluations=fit['evaluations'])
            cases.append(case)
        result=summarize(cases)
        result.update(study='data/'+ID,clock='nominal_200Hz',
            sample_rate_hz=200,noise_seeds=seeds,
            manifest_sha256=study.completion['manifest_sha256'],
            summary_sha256=study.completion['summary_sha256'],
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            charged=study.summary['charged'],original_reads=0,protected_reads=0)
        return result
    finally:study.close()


def render(report):
    lines=['# Generated nominal 200 Hz solver check','',
        f"**{report['passing_fixtures']}/6** generated fixtures passed the "
        'four-fit forecast-agreement gate. '
        f"{report['numerical_stops']}/24 fits passed numerical stopping; "
        f"{report['physical_accuracy_passes']}/24 passed the separate "
        f"generated physical screen; {report['technical_failures']} had "
        'technical failures.','',
        '| Generated model | Calibration | Numerical stops | Physical screen | Largest later-path spread |',
        '|---|---|---:|---:|---:|']
    for row in report['fixture_rows']:
        spread=row['maximum_later_path_spread_m']
        amount='—' if spread is None else f'{spread:.3g} m'
        lines.append(f"| {row['model']} | {row['sensor_case']} | "
            f"{row['numerical_stops']}/4 | {row['physical_accuracy_passes']}/4 | "
            f'{amount} |')
    horizontal=report['maximum_later_horizontal_rms_m']
    vertical=report['maximum_later_height_rms_m']
    if horizontal is not None and vertical is not None:
        lines += ['',f'Largest later RMS error against generated truth: '
                  f'{horizontal:.3g} m horizontal and {vertical:.3g} m in height.']
    lines += ['',
        'This exact 200 Hz grid checks the nominal-clock software path and '
        'matched solver forecasts with distinct noise seeds. Each fit uses '
        '39 earlier receiver reports and predicts 20 withheld reports. '
        'It cannot test sensitivity to irregular packet-header timestamps. '
        'It does not revise aircraft fits or calibrate aircraft prediction '
        'coverage.','',
        '[Frozen plan](NOMINAL_200HZ_SOLVER_PLAN.md) · '
        '[All fit outcomes](nominal-200hz-solver-tasks.csv)']
    return '\n'.join(lines)+'\n'


def publish(root='.'):
    from .studies.artifacts import atomic,encoded
    root=Path(root).resolve();report=build(root)
    output=root/'docs/prediction-group-transfer'
    atomic(output/'NOMINAL_200HZ_SOLVER_RESULT.md',render(report).encode())
    atomic(output/'nominal-200hz-solver-tasks.csv',task_csv(report))
    atomic(output/'nominal-200hz-solver-report.json',encoded(report))
    return report


if __name__=='__main__':
    result=publish()
    print('fixtures:',result['passing_fixtures'],'/',result['fixtures'])
