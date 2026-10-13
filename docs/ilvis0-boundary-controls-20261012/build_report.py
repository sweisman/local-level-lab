# SPDX-License-Identifier: AGPL-3.0-or-later
"""Run the finite software matrix explicitly; default renders saved controls only."""
import argparse
import collections
import csv
import hashlib
import io
import json
import os
import platform
from pathlib import Path

import numpy as np
import scipy

from lll import ilvis0_boundary_controls as controls
from lll.ilvis0_solver_boundary import POLICY
from lll.ilvis0_solver_refinement import POLICY as STOPPING

ROOT = Path(__file__).resolve().parents[2]
GUIDE = Path(__file__).resolve().parent
SOURCES = ('analysis/lll/ilvis0_solver_boundary.py', 'analysis/lll/ilvis0_boundary_controls.py',
           'analysis/lll/ilvis0_solver_rectangular.py', 'analysis/lll/ilvis0_solver_controls.py',
           'analysis/lll/ilvis0_solver_refinement.py', 'analysis/lll/ilvis0_solver_verified_stop.py',
           'analysis/tests/test_ilvis0_solver_boundary.py', 'analysis/tests/test_ilvis0_boundary_controls.py',
           'docs/ilvis0-boundary-controls-20261012/PLAN.md',
           'docs/ilvis0-boundary-controls-20261012/build_report.py')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(value)
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-software-controls', action='store_true')
    args = parser.parse_args()
    results_path = GUIDE/'controls.json'
    if args.run_software_controls:
        if results_path.exists():
            raise ValueError('completed software matrix exists; render without run flag')
        rows = []
        for name in controls.CONTROLS:
            for index in range(4):
                for method in controls.METHODS:
                    row = controls.run_one(name, index, method)
                    row['fit'].pop('local_linearization', None)
                    rows.append(row)
        document = dict(version=controls.VERSION, rows=rows, observed_fit_starts=0,
                        solver_policy=POLICY, unchanged_stopping_policy=STOPPING,
                        maximum_control_calls=120*controls.ALLOWANCE,
                        source_sha256={name: digest(ROOT/name) for name in SOURCES},
                        environment=dict(python=platform.python_version(), numpy=np.__version__,
                                         scipy=scipy.__version__, platform=platform.platform(),
                                         numerical_threads={name: os.environ.get(name) for name in
                                             ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS')}))
        write(results_path, json.dumps(document, indent=2, allow_nan=False)+'\n')
    else:
        document = json.loads(results_path.read_text())
        receipt = json.loads((GUIDE/'receipt.json').read_text())
        if digest(results_path) != receipt['outputs']['controls.json']:
            raise ValueError('saved software controls hash mismatch')
    rows = document['rows']
    if len(rows) != 120 or len({row['identity'] for row in rows}) != 120:
        raise ValueError('incomplete or duplicate software matrix')
    counters = collections.defaultdict(collections.Counter)
    for row in rows:
        counters[row['method']]['calls'] += row['actual_evaluations']
        counters[row['method']]['passed'] += row['passed']
        counters[row['method']]['stopping'] += row['fit']['converged']
    lines = ['# Boundary-aware nonlinear controls', '',
             'This completed software matrix uses ten known-answer controls, four fixed starts',
             'and three numerical strategies. It reads no NASA recordings and changes no archival results.',
             '', '| Strategy | Fresh stopping checks | Known-answer qualification | Actual evaluations |',
             '|---|---:|---:|---:|']
    for method in controls.METHODS:
        count = counters[method]
        lines.append(f"| {method} | {count['stopping']}/40 | {count['passed']}/40 | {count['calls']} |")
    lines += ['', 'Qualification checks both the existing fresh stopping tests and recovery of the',
              'known objective and predicted observations. Unique well-conditioned cases also',
              'check the parameters. A solver stopping successfully is insufficient by itself.',
              '', '| Control | Original | Snapped start | Bounded linear steps |',
              '|---|---:|---:|---:|']
    for name in controls.CONTROLS:
        counts = [sum(row['passed'] for row in rows if row['control'] == name and row['method'] == method)
                  for method in controls.METHODS]
        lines.append(f'| {name} | {counts[0]}/4 | {counts[1]}/4 | {counts[2]}/4 |')
    total = sum(row['actual_evaluations'] for row in rows)
    success = counters['boundary_bvls']['passed'] == 40
    lines += ['', f'The matrix used {total:,} actual evaluations, within its 24,000-call ceiling.',
              'Every run retained its own 200-call limit, including fresh final checks.',
              'No failure or poor start was retried.', '',
              ('The new candidate passes this software matrix.' if success else
               'The new candidate does not pass the complete software matrix.'),
              'Its bounded linear steps are checked against the actual nonlinear cost; rejected',
              'steps are shortened. Only boundary slack of at most one trillionth in normalized',
              'coordinates is snapped. Physical parameter limits and stopping thresholds are unchanged.',
              '', 'These are controls with exact derivatives and known answers, not qualification',
              'on the much larger archival observation model. They establish neither statistical',
              'significance nor recovery of any of the 41 unresolved stretches. A separate finite',
              'observed trial would be needed before rollout.', '',
              'The saved [results](controls.json), [per-run table](controls.csv) and',
              '[receipt](receipt.json) preserve parameters, costs, stationarity, fresh checks,',
              'evaluation counts, source hashes and the numerical environment.',
              'The [fixed plan](PLAN.md) defines the comparison. Default report regeneration reads',
              'the saved results only; it performs no optimization.', '']
    write(GUIDE/'README.md', '\n'.join(lines))
    fields = ('identity', 'control', 'start', 'method', 'passed', 'actual_evaluations',
              'reference_objective', 'objective_error', 'prediction_error',
              'identifiable_parameter_error', 'parameters_at_limits')
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fields)
    writer.writeheader()
    writer.writerows({key: row[key] for key in fields} for row in rows)
    write(GUIDE/'controls.csv', stream.getvalue())
    receipt = dict(version=controls.VERSION, observed_fit_starts=0, scientific_decision='abstain',
                   actual_control_calls=total, maximum_control_calls=24000,
                   source_sha256=document['source_sha256'], environment=document['environment'],
                   outputs={name: digest(GUIDE/name) for name in ('controls.json', 'controls.csv', 'README.md')})
    write(GUIDE/'receipt.json', json.dumps(receipt, indent=2, allow_nan=False)+'\n')
    print(json.dumps(dict(actual_evaluations=total, by_method=dict(counters), observed_fit_starts=0)))


if __name__ == '__main__':
    main()
