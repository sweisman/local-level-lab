# SPDX-License-Identifier: AGPL-3.0-or-later
"""Seal cheap software controls before freezing the separate observed proposal."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    if (ROOT/'data/ilvis0-rectangular-recovery-trial-v2-20261012/manifest.json').exists():
        raise ValueError('software qualification already frozen')
    tests = ['analysis/tests/test_ilvis0_solver_rectangular.py',
             'analysis/tests/test_ilvis0_rectangular_worker.py',
             'analysis/tests/test_ilvis0_recovery_diagnosis.py',
             'analysis/tests/test_ilvis0_recovery_screen.py',
             'analysis/tests/test_ilvis0_recovery_plan.py',
             'analysis/tests/test_ilvis0_recovery_worker.py']
    env = dict(os.environ, PYTHONPATH='analysis', OPENBLAS_NUM_THREADS='2',
               OMP_NUM_THREADS='2', MKL_NUM_THREADS='2')
    result = subprocess.run([sys.executable, '-m', 'pytest', '-q', *tests], cwd=ROOT,
                            env=env, capture_output=True, text=True)
    (HERE/'test-output.txt').write_text(result.stdout+result.stderr)
    if result.returncode:
        raise ValueError('software controls failed; no receipt sealed')
    from lll import runtime
    sources = tests + ['analysis/lll/ilvis0_solver_rectangular.py',
                       'analysis/tests/ilvis0_rectangular_worker.py',
                       'analysis/lll/ilvis0_recovery_diagnosis.py',
                       'analysis/lll/ilvis0_recovery_screen.py',
                       'analysis/lll/ilvis0_solver_refinement.py',
                       'analysis/lll/ilvis0_solver_verified_stop.py',
                       'analysis/lll/ilvis0_solver_controls.py',
                       'analysis/lll/ilvis0_solver_screen.py',
                       'analysis/lll/ilvis0_estimator_controls.py',
                       str(Path(__file__).relative_to(ROOT))]
    report = dict(version='ilvis0-rectangular-controls-v1', exit_code=0,
                  observed_fit_starts=0, original_records_decoded=0,
                  numerical_environment=runtime.numerical_environment(),
                  scientific_decision='abstain')
    (HERE/'control-results.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    receipt = dict(sources={str((ROOT/n).resolve()): sha(ROOT/n) for n in sources},
                   numerical_environment=report['numerical_environment'],
                   artifacts={n: sha(HERE/n) for n in ('CONTROL.md', 'control-results.json', 'test-output.txt')})
    (HERE/'control-receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
    print(result.stdout.strip())


if __name__ == '__main__':
    main()
