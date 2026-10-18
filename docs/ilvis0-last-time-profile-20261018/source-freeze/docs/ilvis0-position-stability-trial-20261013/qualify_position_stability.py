# SPDX-License-Identifier: AGPL-3.0-or-later
"""Seal deterministic controls and worker checks before the new observed freeze."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

from lll import ilvis0_solver_position as solver, runtime

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    if (ROOT/'data/ilvis0-position-stability-trial-20261013/manifest.json').exists():
        raise ValueError('software qualification already frozen')
    tests = ['analysis/tests/test_ilvis0_solver_position.py',
             'analysis/tests/test_ilvis0_position_stability_worker.py',
             'analysis/tests/test_ilvis0_solver_boundary.py',
             'analysis/tests/test_ilvis0_boundary_worker.py',
             'analysis/tests/test_ilvis0_recovery_plan.py',
             'analysis/tests/test_ilvis0_recovery_worker.py']
    env = dict(os.environ, PYTHONPATH='analysis', OPENBLAS_NUM_THREADS='2',
               OMP_NUM_THREADS='2', MKL_NUM_THREADS='2')
    result = subprocess.run([sys.executable, '-m', 'pytest', '-q', '--tb=short',
                            '--junitxml='+str(HERE/'controls.xml'), *tests],
                            cwd=ROOT, env=env, capture_output=True, text=True)
    (HERE/'test-output.txt').write_text(result.stdout+result.stderr)
    if result.returncode:
        raise ValueError('software qualification failed; no receipt sealed')
    cases = list(ET.parse(HERE/'controls.xml').getroot().iter('testcase'))
    known = [case for case in cases if case.get('name', '').startswith('test_known_objectives_predictions_and_budget[')]
    if len(known) != 40 or any(list(case) for case in cases):
        raise ValueError('missing, failed or skipped qualification checks')
    sources = {str((ROOT/name).resolve()): sha(ROOT/name) for name in tests}
    for path in (Path(solver.__file__), ROOT/'analysis/tests/ilvis0_position_stability_worker.py', Path(__file__)):
        sources[str(path.resolve())] = sha(path)
    report = dict(version='ilvis0-position-stability-controls-v1', exit_code=0,
                  solver_version=solver.VERSION, known_answer_passes=40,
                  total_checks=len(cases), observed_fit_starts=0, original_records_decoded=0,
                  numerical_environment=runtime.numerical_environment(), scientific_decision='abstain')
    (HERE/'control-results.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    receipt = dict(sources=sources, numerical_environment=report['numerical_environment'],
                   artifacts={name: sha(HERE/name) for name in
                              ('CONTROL.md', 'control-results.json', 'test-output.txt', 'controls.xml')})
    (HERE/'control-receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
    print(result.stdout.strip())


if __name__ == '__main__':
    main()
