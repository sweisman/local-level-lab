# SPDX-License-Identifier: AGPL-3.0-or-later
"""Run one finite analytic screen, or render its saved evidence without solving."""
import argparse
import csv
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import scipy
from lll import ilvis0_solver_screen as screen
from lll import ilvis0_solver_controls as controls
from lll import ilvis0_solver_refinement as solver

HERE=Path(__file__).resolve().parent


def sha(path):
    with path.open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--render-only',action='store_true'); args=parser.parse_args()
    result=HERE/'solver-screen.json'; receipt=HERE/'solver-screen-receipt.json'
    sources=[Path(__file__).resolve(),Path(screen.__file__).resolve(),Path(controls.__file__).resolve(),Path(solver.__file__).resolve()]
    if not args.render_only:
        if result.exists(): raise ValueError('completed analytic screen is frozen; use --render-only')
        out=screen.run()
        result.write_text(json.dumps(out,sort_keys=True,indent=2,allow_nan=False)+'\n')
        receipt.write_text(json.dumps(dict(version=screen.VERSION,observed_fit_starts=0,native_predictions=0,
            software_starts=72,environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__),
            sources={str(p.resolve()):sha(p) for p in sources},result_sha256=sha(result)),sort_keys=True,indent=2)+'\n')
    proof=json.loads(receipt.read_text()); out=json.loads(result.read_text())
    if proof['result_sha256']!=sha(result): raise ValueError('screen result hash differs')
    for name,digest in proof['sources'].items():
        if sha(Path(name))!=digest: raise ValueError('screen source hash differs')
    rows=out['results']
    with (HERE/'solver-screen.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)
    lines=['# Analytic solver screen','',
        'This small software test uses independently known optima, not NASA measurements. '
        'It compares dense least squares with Jacobian scaling, dense least squares with '
        'unit scaling, and regularized iterative least squares. All have the same box '
        'constraints, stopping tolerances and 200-evaluation cap. There are eight '
        'controls and three deterministic starts per variant, including two 27-parameter '
        'controls with a Jacobian condition ratio of 50 million.','',
        'Passing requires solver success, a fresh stationarity check, agreement with the '
        'known objective and predicted residuals, and parameter recovery where unique. '
        'A success flag alone does not pass. These controls do not qualify full airborne '
        'integration, its staged initialization, or a global model optimum.','',
        '| Variant | Passed / 24 | Recorded evaluations |','|---|---:|---:|']
    for variant in screen.VARIANTS:
        part=[r for r in rows if r['variant']==variant]
        lines.append(f"| {variant} | {sum(r['passed'] for r in part)} / 24 | {sum(r['evaluations'] for r in part)} |")
    failed=[r for r in rows if not r['passed']]
    lines+=['','## Preserved failures','']
    for r in failed:
        lines.append(f"- {r['identity']}: {r['message']} Objective {r['objective']:.6g}, "
            f"residual error {r['residual_error_to_known_optimum']:.6g}, stationarity {r['stationarity']:.6g}.")
    if not failed: lines.append('None in this finite screen.')
    lines+=['','[Complete results](solver-screen.csv) preserve every control. The screen '
        'makes **zero observed fit starts and zero native predictions**. Its completed '
        'evidence is frozen; `--render-only` regenerates this page without solving.','']
    (HERE/'SOLVER_SCREEN.md').write_text('\n'.join(lines))
    print(json.dumps({v:dict(passed=sum(r['passed'] for r in rows if r['variant']==v),total=24)
        for v in screen.VARIANTS},sort_keys=True))


if __name__=='__main__': main()
