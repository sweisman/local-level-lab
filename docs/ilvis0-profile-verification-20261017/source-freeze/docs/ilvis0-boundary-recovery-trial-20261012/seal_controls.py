# SPDX-License-Identifier: AGPL-3.0-or-later
"""Seal launcher tests and the completed matrix; never rerun that matrix."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from lll import ilvis0_solver_boundary as solver, runtime

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MATRIX = ROOT/'docs/ilvis0-boundary-controls-20261012'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    if (ROOT/'data/ilvis0-boundary-recovery-trial-20261012/manifest.json').exists():
        raise ValueError('software qualification already frozen')
    saved = json.loads((MATRIX/'controls.json').read_text())
    receipt = json.loads((MATRIX/'receipt.json').read_text())
    for name, digest in receipt['outputs'].items():
        if sha(MATRIX/name) != digest:
            raise ValueError('completed matrix output mismatch')
    for name, digest in receipt['source_sha256'].items():
        if sha(ROOT/name) != digest:
            raise ValueError('completed matrix source mismatch')
    selected = [r for r in saved['rows'] if r['method'] == 'boundary_bvls']
    if len(selected) != 40 or len({r['identity'] for r in selected}) != 40 or not all(r['passed'] for r in selected):
        raise ValueError('known-answer software qualification unfinished')
    tests = ['analysis/tests/test_ilvis0_solver_boundary.py',
             'analysis/tests/test_ilvis0_boundary_controls.py',
             'analysis/tests/test_ilvis0_boundary_worker.py',
             'analysis/tests/test_ilvis0_recovery_plan.py',
             'analysis/tests/test_ilvis0_recovery_worker.py']
    env = dict(os.environ, PYTHONPATH='analysis', OPENBLAS_NUM_THREADS='2',
               OMP_NUM_THREADS='2', MKL_NUM_THREADS='2')
    result = subprocess.run([sys.executable, '-m', 'pytest', '-q', *tests], cwd=ROOT,
                            env=env, capture_output=True, text=True)
    (HERE/'test-output.txt').write_text(result.stdout+result.stderr)
    if result.returncode:
        raise ValueError('launcher controls failed; no receipt sealed')
    sources = {str((ROOT/name).resolve()): digest for name, digest in receipt['source_sha256'].items()
               if name.startswith('analysis/')}
    for name in tests+['analysis/tests/ilvis0_boundary_worker.py', str(Path(__file__).relative_to(ROOT))]:
        sources[str((ROOT/name).resolve())] = sha(ROOT/name)
    report = dict(version='ilvis0-boundary-worker-controls-v1', exit_code=0,
                  solver_version=solver.VERSION, known_answer_passes=40,
                  observed_fit_starts=0, original_records_decoded=0,
                  matrix_path=str((MATRIX/'controls.json').resolve()),
                  matrix_sha256=sha(MATRIX/'controls.json'),
                  numerical_environment=runtime.numerical_environment(), scientific_decision='abstain')
    (HERE/'control-results.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    (HERE/'matrix-receipt.json').write_bytes((MATRIX/'receipt.json').read_bytes())
    sealed = dict(sources=sources, numerical_environment=report['numerical_environment'],
                  artifacts={name: sha(HERE/name) for name in
                      ('CONTROL.md', 'control-results.json', 'test-output.txt', 'matrix-receipt.json')})
    (HERE/'control-receipt.json').write_text(json.dumps(sealed, indent=2, sort_keys=True)+'\n')
    print(result.stdout.strip())


if __name__ == '__main__':
    main()
