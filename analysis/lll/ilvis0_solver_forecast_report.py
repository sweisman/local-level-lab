# SPDX-License-Identifier: AGPL-3.0-or-later
"""Hash-checked packaging for the generated solver forecast controls."""

import csv
import hashlib
import io
import statistics
from pathlib import Path

import numpy as np

from .ilvis0_solver_forecast_controls import compare_rows
from .ilvis0_solver_forecast_study import ID,MODELS,CLOCKS,tasks


def verify_saved_truth(case,fixture):
    later=np.asarray(case['later_path'],float)
    truth=np.asarray(fixture['gps'],float)[16:]
    metric=np.asarray(fixture['metric'],float)
    if (later.shape!=(8,3) or truth.shape!=(8,3) or metric.shape!=(3,) or
            not np.array_equal(np.asarray(case['metric'],float),metric) or
            not np.all(np.isfinite(later))):
        raise ValueError('saved generated forecast shape or metric differs')
    error=float(np.max(np.linalg.norm((later-truth)*metric,axis=1)))
    if abs(error-case['later_truth_maximum_error_m'])>1e-9:
        raise ValueError('saved later truth score differs')
    return error


def summarize(cases):
    expected={task['identity']:task for task in tasks()}
    if (not isinstance(cases,list) or len(cases)!=24 or
            len({case['identity'] for case in cases})!=24 or
            {case['identity'] for case in cases}!=set(expected)):
        raise ValueError('exact 24-task solver forecast grid required')
    groups={}
    for case in cases:
        if any(case.get(key)!=value for key,value in
               expected[case['identity']]['payload'].items()):
            raise ValueError('frozen task label differs')
        groups.setdefault((case['model'],case['clock']),[]).append(case)
    result=[]
    for model in MODELS:
        for clock in CLOCKS:
            rows=groups[(model,clock)]
            if any(row.get('technical_error') for row in rows):
                comparison=dict(passed=False,all_numerically_stopped=False,
                    all_objectives_within_known_reference=False,
                    maximum_later_path_spread_m=None,
                    scientific_decision='abstain')
            else:
                comparison=compare_rows(rows)
            result.append(dict(model=model,clock=clock,**comparison))
    errors=[case['later_truth_maximum_error_m'] for case in cases
            if case.get('later_truth_maximum_error_m') is not None]
    passed=sum(row['passed'] for row in result)
    return dict(version='ilvis0-generated-solver-forecast-report-v1',
        tasks=24,fixtures=6,passing_fixtures=passed,passed=passed==6,
        numerical_stops=sum(case.get('converged') is True for case in cases),
        technical_failures=sum(bool(case.get('technical_error')) for case in cases),
        maximum_truth_forecast_error_m=max(errors) if errors else None,
        median_truth_forecast_error_m=statistics.median(errors) if errors else None,
        fixture_rows=result,task_rows=cases,observed_fit_starts=0,
        coverage_calibrated=False,scientific_decision='abstain')


def build(root='.'):
    from . import ilvis0_geographic_controls as geographic
    from .studies.artifacts import digest
    from .studies.closed import ClosedStudy
    root=Path(root).resolve()
    study=ClosedStudy(root,'data/'+ID)
    try:
        if (study.completion['state'] not in ('complete','terminal') or
                len(study.tasks)!=24 or len(study.rows)!=24 or
                study.manifest['limits']['maximum_identities']!=24):
            raise ValueError('exact sealed generated solver study required')
        generator='analysis/lll/ilvis0_geographic_controls.py'
        if digest((root/generator).read_bytes())!=study.manifest['sources'][generator]:
            raise ValueError('generated truth source differs from freeze')
        cases=[]
        fixtures={}
        for identity,task in study.tasks.items():
            envelope=study.envelope(identity)
            outcome=envelope['result']
            case=dict(identity=identity,**task['payload'])
            if 'fit.json' not in {name.rsplit('/',1)[-1]
                                  for name in envelope['artifacts']}:
                case.update(technical_error=outcome.get('error','missing fit'))
            else:
                fit=study.artifact(identity,'fit.json')
                path=study.artifact(identity,'later-path.json')
                if (path['training_epochs']!=16 or
                        path['later_receiver_positions_used'] or
                        fit['converged']!=outcome['converged'] or
                        fit['residual_sum_squares']!=outcome['training_cost']):
                    raise ValueError('saved fit/forecast record differs')
                case.update(converged=fit['converged'],
                    training_cost=outcome['training_cost'],
                    known_cost=outcome['known_cost'],
                    later_truth_maximum_error_m=outcome['later_truth_maximum_error_m'],
                    metric=path['metric'],later_path=path['coordinates'],
                    evaluations=fit['evaluations'])
                key=(case['model'],case['clock'])
                if key not in fixtures:
                    fixtures[key]=geographic.fixture(*key)
                verify_saved_truth(case,fixtures[key])
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
    lines=['# Generated solver forecast check','',
        f"**{report['passing_fixtures']}/6** fixtures pass the frozen "
        'four-fit forecast-agreement gate. '
        f"{report['numerical_stops']}/24 fits passed their numerical stopping "
        f"checks; {report['technical_failures']} had technical failures.",'',
        '| Generated model | Clock | Four-fit gate | Maximum path spread |',
        '|---|---|---:|---:|']
    for row in report['fixture_rows']:
        spread=row['maximum_later_path_spread_m']
        lines.append(f"| {row['model']} | {row['clock']} | "
                     f"{'pass' if row['passed'] else 'fail'} | "
                     f"{spread:.3g} m |" if spread is not None else
                     f"| {row['model']} | {row['clock']} | fail | — |")
    lines += ['',
        f"The largest error against the generated later trajectory is "
        f"{report['maximum_truth_forecast_error_m']:.3g} m. This is a software "
        'known-answer error, not aircraft positioning accuracy.','',
        'These are independently generated, 12-second software controls. '
        'Only the first 16 receiver positions entered each fit; the final '
        'eight scored the saved forecast. The original and verified-stop '
        'solvers used identical inputs and physical bounds from zero and '
        'opposed starts. This does not reclassify any observed fit or '
        'calibrate aircraft prediction uncertainty.','',
        '[Frozen plan](GENERATED_SOLVER_FORECAST_PLAN.md) · '
        '[All tasks](generated-solver-forecast-tasks.csv)']
    return '\n'.join(lines)+'\n'


def task_csv(report):
    fields=('identity','model','clock','strategy','start','converged',
            'training_cost','known_cost','later_truth_maximum_error_m',
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
    result=build(root)
    output=root/'docs/prediction-group-transfer'
    atomic(output/'GENERATED_SOLVER_FORECAST_RESULT.md',render(result).encode())
    atomic(output/'generated-solver-forecast-tasks.csv',task_csv(result))
    atomic(output/'generated-solver-forecast-report.json',encoded(result))
    return result


if __name__=='__main__':
    result=publish()
    print('fixtures:',result['passing_fixtures'],'/',result['fixtures'])
