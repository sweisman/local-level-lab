# SPDX-License-Identifier: AGPL-3.0-or-later
"""Publish the sealed distinct bounded-optimizer generated comparison."""

import hashlib
from pathlib import Path

from . import ilvis0_solver_matrix_report_core as core
from .ilvis0_long_solver_report import task_csv
from .ilvis0_independent_solver_study import ID,recipes,tasks


def summarize(cases):
    result=core.summarize(cases,tasks=tasks,recipes=recipes,
        total_epochs=59,training_epochs=39,
        spread_limit_m=.1,cost_range_limit=.01)
    result['version']='ilvis0-independent-solver-report-v1'
    return result


def build(root='.'):
    result=core.build(root,study_id=ID,tasks=tasks,recipes=recipes,
        total_epochs=59,training_epochs=39,
        spread_limit_m=.1,cost_range_limit=.01)
    result.update(version='ilvis0-independent-solver-report-v1',
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        optimizer_families=['trust_region_bounded','scipy_trf'],
        thresholds=dict(maximum_later_path_spread_m=.1,
                        maximum_training_cost_range=.01))
    return result


def render(report):
    lines=['# Independent bounded-optimizer forecast control','',
        f"**{report['passing_fixtures']}/6** generated fixtures passed the "
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
        'SciPy TRF is a different bounded optimizer from the existing '
        'trust-region method. Each fit uses 39 earlier receiver reports and '
        'predicts 20 withheld reports. The six histories have distinct noise '
        'seeds but use one generator family. Agreement here qualifies '
        'only this generated numerical control; it cannot establish a global '
        'optimum, aircraft prediction coverage or a scientific decision. '
        'The 50 original nonpassing aircraft fit labels are unchanged.','',
        '[Frozen plan](INDEPENDENT_SOLVER_PLAN.md) · '
        '[All fit outcomes](independent-solver-tasks.csv) · '
        '[Earlier scope correction](SOLVER_INDEPENDENCE_ERRATUM.md)']
    return '\n'.join(lines)+'\n'


def publish(root='.'):
    from .studies.artifacts import atomic,encoded
    root=Path(root).resolve();report=build(root)
    output=root/'docs/prediction-group-transfer'
    atomic(output/'INDEPENDENT_SOLVER_RESULT.md',render(report).encode())
    atomic(output/'independent-solver-tasks.csv',task_csv(report))
    atomic(output/'independent-solver-report.json',encoded(report))
    return report


if __name__=='__main__':
    result=publish()
    print('fixtures:',result['passing_fixtures'],'/',result['fixtures'])
