# SPDX-License-Identifier: AGPL-3.0-or-later
"""Publish the sealed 120-second distinct-optimizer generated comparison."""

import hashlib
import json
from contextlib import ExitStack
from pathlib import Path

from . import ilvis0_solver_matrix_report_core as core
from .ilvis0_long_solver_report import task_csv
from .ilvis0_long_independent_solver_study import ID,recipes,tasks

RECOVERY='data/'+ID+'-recovery-v2'


def summarize(cases):
    result=core.summarize(cases,tasks=tasks,recipes=recipes,
        total_epochs=119,training_epochs=79,
        spread_limit_m=.1,cost_range_limit=.01)
    result['version']='ilvis0-long-independent-solver-report-v1'
    return result


def select_completed(studies,expected):
    selected={}
    for study in studies:
        for identity,row in study.rows.items():
            if identity not in expected or study.tasks[identity]['payload']!=expected[identity]['payload']:
                raise ValueError('recovery task differs from original task')
            if row['status']=='complete':
                if identity in selected:
                    raise ValueError('duplicate completed generated identity')
                selected[identity]=study
    if set(selected)!=set(expected):
        raise ValueError('all original generated identities must complete')
    return selected


def build(root='.'):
    from .studies.closed import ClosedStudy
    from .studies.task_resume import resume_campaign
    root=Path(root).resolve()
    recovery=resume_campaign(root,root/RECOVERY,launch=False)
    if recovery['state']!='all_tasks_finished':
        raise ValueError('complete, verified recovery required before reporting')
    recovery_plan=json.loads((root/RECOVERY/'plan.json').read_bytes())
    expected={task['identity']:task for task in tasks()}
    with ExitStack() as stack:
        studies=[ClosedStudy(root,'data/'+ID)]
        studies.extend(ClosedStudy(root,RECOVERY+f'/stage-{index:03d}')
                       for index in range(recovery['stages']))
        for study in studies:stack.callback(study.close)
        parent=studies[0]
        if (set(parent.tasks)!=set(expected) or
                {key:parent.input(key) for key in recipes()}!=recipes()):
            raise ValueError('original generated source tasks or inputs changed')
        selected=select_completed(studies,expected)
        cases=[core.case_from_study(selected[identity],identity,task,
                    total_epochs=119,training_epochs=79)
               for identity,task in expected.items()]
        result=summarize(cases)
        result.update(study='data/'+ID,recovery=RECOVERY,
            parent_manifest_sha256=parent.completion['manifest_sha256'],
            stage_manifest_sha256=[study.completion['manifest_sha256'] for study in studies[1:]],
            prior_interrupted_charges=recovery_plan['prior_interrupted_charges'],
            technical_interruptions=recovery['technical_interruptions'],
            charged={key:sum(study.summary['charged'][key] for study in studies)
                     for key in parent.summary['charged']},
            original_reads=0,protected_reads=0)
    result.update(version='ilvis0-long-independent-solver-report-v1',
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        optimizer_families=['trust_region_bounded','scipy_trf'],
        thresholds=dict(maximum_later_path_spread_m=.1,
                        maximum_training_cost_range=.01))
    return result


def render(report):
    lines=['# Longer independent-optimizer forecast control','',
        f"**{report['passing_fixtures']}/6** generated histories passed the "
        'preregistered numerical agreement gate. '
        f"{report['numerical_stops']}/24 fits passed their unchanged final "
        f"stopping checks; {report['physical_accuracy_passes']}/24 passed "
        f"the separate generated physical screen; {report['technical_failures']} "
        'had technical failures.','',
        '| Generated model | Clock | Numerical stops | Physical screen | Largest later-path spread | Training cost range |',
        '|---|---|---:|---:|---:|---:|']
    for row in report['fixture_rows']:
        spread=row['maximum_later_path_spread_m']
        cost=row['maximum_training_cost_range']
        lines.append(f"| {row['model']} | {row['clock']} | "
            f"{row['numerical_stops']}/4 | {row['physical_accuracy_passes']}/4 | "
            f"{'—' if spread is None else f'{spread:.3g} m'} | "
            f"{'—' if cost is None else f'{cost:.3g}'} |")
    horizontal=report['maximum_later_horizontal_rms_m']
    vertical=report['maximum_later_height_rms_m']
    if horizontal is not None and vertical is not None:
        lines += ['',f'Largest later RMS error against generated truth: '
                  f'{horizontal:.3g} m horizontal and {vertical:.3g} m in height.']
    lines += ['',
        'SciPy TRF and the custom trust-region solver are separate bounded '
        'optimizers. Each fit uses 79 earlier receiver reports to predict 40 '
        'withheld reports over a 120-second generated history. The six '
        'histories have distinct noise seeds but one generator family. '
        'This numerical control cannot establish a global optimum, aircraft '
        'prediction coverage or a scientific decision. The original 50 '
        'nonpassing aircraft fit labels remain unchanged. A host interruption '
        'left two charged starts unfinished; the original allowance is sealed '
        'and the four missing identities were completed under a separately '
        'qualified finite recovery. No completed task was repeated.','',
        '[Frozen plan](LONG_INDEPENDENT_SOLVER_PLAN.md) · '
        '[All fit outcomes](long-independent-solver-tasks.csv) · '
        '[Earlier scope correction](SOLVER_INDEPENDENCE_ERRATUM.md)']
    return '\n'.join(lines)+'\n'


def publish(root='.'):
    from .studies.artifacts import atomic,encoded
    root=Path(root).resolve();report=build(root)
    output=root/'docs/prediction-group-transfer'
    atomic(output/'LONG_INDEPENDENT_SOLVER_RESULT.md',render(report).encode())
    atomic(output/'long-independent-solver-tasks.csv',task_csv(report))
    atomic(output/'long-independent-solver-report.json',encoded(report))
    return report


if __name__=='__main__':
    result=publish()
    print('fixtures:',result['passing_fixtures'],'/',result['fixtures'])
