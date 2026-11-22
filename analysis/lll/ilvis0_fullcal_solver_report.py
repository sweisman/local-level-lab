# SPDX-License-Identifier: AGPL-3.0-or-later
"""Describe the sealed full-calibration generated pilot without refitting."""

import csv
import hashlib
import io
import math
from pathlib import Path

import numpy as np

from .ilvis0_fullcal_solver_pilot import ID,SOLVERS,tasks
from .ilvis0_solver_position import physical_metric


def compare(cases):
    expected={task['identity'] for task in tasks()}
    if (not isinstance(cases,list) or len(cases)!=4 or
            {row['identity'] for row in cases}!=expected or
            len({row['identity'] for row in cases})!=4):
        raise ValueError('exact four generated solver identities required')
    technical=sum(bool(row.get('technical_error')) for row in cases)
    stops=sum(row.get('converged') is True for row in cases)
    physical=sum(row.get('physical_accuracy_passed') is True for row in cases)
    spread=None
    if technical==0:
        paths=[np.asarray(row['forecast'],float) for row in cases]
        if any(path.shape!=(59,3) or not np.all(np.isfinite(path))
               for path in paths):
            raise ValueError('complete finite saved forecast paths required')
        metric=physical_metric(paths[0][39:])
        spread=max(float(np.max(np.linalg.norm((a[39:]-b[39:])*metric,axis=1)))
                   for index,a in enumerate(paths) for b in paths[index+1:])
    rows=[{key:row.get(key) for key in
           ('identity','solver','start','converged','physical_accuracy_passed',
            'training_cost','prediction_horizontal_rms_m',
            'prediction_vertical_rms_m','technical_error','evaluations')}
          for row in cases]
    return dict(version='ilvis0-fullcal-solver-pilot-report-v1',
        tasks=4,technical_failures=technical,numerical_stops=stops,
        physical_accuracy_passes=physical,
        maximum_later_path_spread_m=spread,task_rows=rows,
        scientific_decision='abstain',coverage_calibrated=False,
        observed_fit_starts=0)


def build(root='.'):
    from .studies.closed import ClosedStudy
    root=Path(root).resolve()
    study=ClosedStudy(root,'data/'+ID)
    try:
        if (study.completion['state'] not in ('complete','terminal') or
                len(study.tasks)!=4 or len(study.rows)!=4 or
                study.manifest['limits']['maximum_identities']!=4):
            raise ValueError('exact sealed four-task full-calibration pilot required')
        cases=[]
        for identity,task in study.tasks.items():
            outcome=study.envelope(identity)['result']
            payload=task['payload']
            case=dict(identity=identity,solver=payload['solver'],
                      start=payload['start'])
            names={name.rsplit('/',1)[-1]
                   for name in study.envelope(identity)['artifacts']}
            if not {'fit.json','forecast.json'}<=names:
                case['technical_error']=outcome.get('reason','missing saved fit or forecast')
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
                    raise ValueError('sealed training/forecast record differs')
                case.update(converged=fit['converged'],
                    physical_accuracy_passed=outcome['physical_accuracy_passed'],
                    training_cost=outcome['training_cost'],
                    prediction_horizontal_rms_m=outcome['prediction']['horizontal_rms_m'],
                    prediction_vertical_rms_m=outcome['prediction']['vertical_rms_m'],
                    forecast=forecast['coordinates'],
                    evaluations=fit['evaluations'])
            cases.append(case)
        report=compare(cases)
        report.update(study='data/'+ID,
            manifest_sha256=study.completion['manifest_sha256'],
            summary_sha256=study.completion['summary_sha256'],
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            charged=study.summary['charged'],original_reads=0,protected_reads=0)
        return report
    finally:study.close()


def render(report):
    spread=report['maximum_later_path_spread_m']
    lines=['# Full-calibration generated solver pilot','',
        f"The study completed {report['tasks']} fixed task identities. "
        f"{report['numerical_stops']}/4 fits passed numerical stopping, "
        f"{report['physical_accuracy_passes']}/4 passed the separately "
        'declared physical accuracy screen, and '
        f"{report['technical_failures']} had technical failures.",'',
        ('Largest later-path separation among the four saved fits: '
         f'{spread:.3g} m.' if spread is not None else
         'Later-path separation is unavailable after a technical failure.'),'',
        '| Solver | Start | Numerical stop | Physical screen | Training cost | Later horizontal RMS | Later height RMS |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for row in sorted(report['task_rows'],key=lambda x:(x['solver'],x['start'])):
        cost=row['training_cost']
        horizontal=row['prediction_horizontal_rms_m']
        vertical=row['prediction_vertical_rms_m']
        lines.append(f"| {row['solver']} | {row['start']} | "
            f"{'yes' if row['converged'] else 'no'} | "
            f"{'yes' if row['physical_accuracy_passed'] else 'no'} | "
            f"{cost:.6g} | {horizontal:.3g} m | {vertical:.3g} m |"
            if cost is not None else
            f"| {row['solver']} | {row['start']} | no | no | — | — | — |")
    lines += ['',
        'All four tasks use the same independently generated noisy flight, '
        'full 26-parameter calibration box and earlier-only receiver cut. '
        'This is a development diagnostic: solver agreement is not aircraft accuracy. '
        'The physical screen here compares generated paths with known truth; a '
        'small training cost is not a withheld-position accuracy claim. '
        'Observed aircraft fits and the reserved ESA confirmation groups '
        'remain unchanged.','',
        '[Frozen pilot plan](FULL_CALIBRATION_SOLVER_NEXT.md) · '
        '[All task outcomes](fullcal-solver-pilot-tasks.csv)']
    return '\n'.join(lines)+'\n'


def task_csv(report):
    fields=('identity','solver','start','converged',
            'physical_accuracy_passed','training_cost',
            'prediction_horizontal_rms_m','prediction_vertical_rms_m','technical_error',
            'evaluations')
    stream=io.StringIO(newline='')
    writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n')
    writer.writeheader()
    for row in report['task_rows']:
        writer.writerow({key:row.get(key) for key in fields})
    return stream.getvalue().encode()


def publish(root='.'):
    from .studies.artifacts import atomic,encoded
    root=Path(root).resolve()
    result=build(root)
    output=root/'docs/prediction-group-transfer'
    atomic(output/'FULL_CALIBRATION_SOLVER_RESULT.md',render(result).encode())
    atomic(output/'fullcal-solver-pilot-tasks.csv',task_csv(result))
    atomic(output/'fullcal-solver-pilot-report.json',encoded(result))
    return result


if __name__=='__main__':
    result=publish()
    print('numerical stops:',result['numerical_stops'],'/',result['tasks'])
