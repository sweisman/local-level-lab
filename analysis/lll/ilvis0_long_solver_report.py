# SPDX-License-Identifier: AGPL-3.0-or-later
"""Publish the sealed longer generated solver confirmation."""

import csv
import hashlib
import io
from pathlib import Path

from . import ilvis0_solver_matrix_report_core as core
from .ilvis0_long_solver_study import ID,recipes,tasks


def summarize(cases):
    value=core.summarize(cases,tasks=tasks,recipes=recipes,
        total_epochs=119,training_epochs=79,
        spread_limit_m=.1,cost_range_limit=.01)
    value['version']='ilvis0-long-solver-confirmation-report-v1'
    return value


def build(root='.'):
    value=core.build(root,study_id=ID,tasks=tasks,recipes=recipes,
        total_epochs=119,training_epochs=79,
        spread_limit_m=.1,cost_range_limit=.01)
    value.update(version='ilvis0-long-solver-confirmation-report-v1',
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        thresholds=dict(maximum_later_path_spread_m=.1,
                        maximum_training_cost_range=.01))
    return value


def render(report):
    lines=['# Longer generated solver confirmation','',
        f"**{report['passing_fixtures']}/6** generated histories passed the "
        'preregistered numerical gate. '
        f"{report['numerical_stops']}/24 fits passed stopping, "
        f"{report['physical_accuracy_passes']}/24 passed the separate "
        f"generated physical screen, and {report['technical_failures']} "
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
        'Each fit uses 79 earlier receiver reports and predicts 40 withheld '
        'reports over a 120-second generated history. The six histories use '
        'distinct noise seeds but one declared generator family. Close solver '
        'paths and training costs qualify a numerical method on these inputs; '
        'they do not establish aircraft prediction coverage. The original '
        '50 nonpassing aircraft labels and protected ESA flights are unchanged.','',
        '[Frozen plan](LONG_HORIZON_SOLVER_PLAN.md) · '
        '[All fit outcomes](long-solver-tasks.csv)']
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
    root=Path(root).resolve();report=build(root)
    output=root/'docs/prediction-group-transfer'
    atomic(output/'LONG_HORIZON_SOLVER_RESULT.md',render(report).encode())
    atomic(output/'long-solver-tasks.csv',task_csv(report))
    atomic(output/'long-solver-report.json',encoded(report))
    return report


if __name__=='__main__':
    result=publish()
    print('fixtures:',result['passing_fixtures'],'/',result['fixtures'])
