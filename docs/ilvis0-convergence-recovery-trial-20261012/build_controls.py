# SPDX-License-Identifier: AGPL-3.0-or-later
"""Run cheap deterministic software checks and seal the launcher's qualification."""
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
    if (ROOT / 'data/ilvis0-convergence-recovery-trial-20261012/manifest.json').exists():
        raise RuntimeError('controls are already frozen; use a new study for changes')
    env = dict(os.environ, PYTHONPATH='analysis', OPENBLAS_NUM_THREADS='2',
               OMP_NUM_THREADS='2', MKL_NUM_THREADS='2')
    tests = ['analysis/tests/test_ilvis0_solver_recovery.py',
             'analysis/tests/test_ilvis0_recovery_plan.py',
             'analysis/tests/test_ilvis0_recovery_worker.py']
    result = subprocess.run([sys.executable, '-m', 'pytest', '-q', *tests], cwd=ROOT,
                            env=env, capture_output=True, text=True)
    (HERE / 'test-output.txt').write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError('software controls failed; no qualification receipt written')
    from lll import runtime
    sources = tests + ['analysis/lll/ilvis0_solver_recovery.py',
                       'analysis/lll/ilvis0_recovery_plan.py',
                       'analysis/tests/ilvis0_recovery_worker.py',
                       str(Path(__file__).relative_to(ROOT))]
    report = dict(version='ilvis0-recovery-controls-v1', exit_code=result.returncode,
                  observed_fit_starts=0, original_records_decoded=0,
                  numerical_environment=runtime.numerical_environment(),
                  scope='software-only; full archival optimizer qualification awaits the observed trial',
                  scientific_decision='abstain')
    (HERE / 'control-results.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    receipt = dict(version=report['version'], sources={str((ROOT / name).resolve()): sha(ROOT / name) for name in sources},
                   numerical_environment=report['numerical_environment'],
                   artifacts={name: sha(HERE / name) for name in ('CONTROL.md', 'control-results.json', 'test-output.txt')})
    (HERE / 'control-receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print(result.stdout.strip())


if __name__ == '__main__':
    main()
