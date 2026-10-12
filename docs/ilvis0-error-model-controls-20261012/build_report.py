# SPDX-License-Identifier: AGPL-3.0-or-later
"""Run small covariance software controls; never load or fit NASA recordings."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import numpy as np

from lll import ilvis0_error_model as model, runtime

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
TEST=ROOT/'analysis/tests/test_ilvis0_error_model.py'
PLAN=ROOT/'docs/ilvis0-residual-covariance-20261012/ERROR_MODEL_PLAN.md'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build():
    sources=[Path(__file__).resolve(),Path(model.__file__).resolve(),TEST,Path(runtime.__file__).resolve()]
    initial={str(p):sha(p) for p in sources+[PLAN]}
    # The qualification suite uses matrices of at most nine rows, no random campaign.
    run=subprocess.run([sys.executable,'-m','pytest','-q',str(TEST),'--tb=short'],
        cwd=ROOT,env={**os.environ,'PYTHONPATH':str(ROOT/'analysis'),
            'OPENBLAS_NUM_THREADS':'2','OMP_NUM_THREADS':'2','MKL_NUM_THREADS':'2'},
        text=True,capture_output=True,timeout=60)
    if run.returncode or run.stderr or '35 passed' not in run.stdout:
        raise RuntimeError('Covariance qualification failed:\n'+run.stdout+run.stderr)
    if any(sha(Path(p))!=expected for p,expected in initial.items()):
        raise ValueError('qualification source/plan changed during execution')
    passed=int(re.search(r'(\d+) passed',run.stdout)[1])
    c=np.array([[4.,2.],[2.,9.]])
    prediction=model.condition(c,[0],[1],[2.])
    whitening=model.whiten([2.,4.],[[4.,2.],[2.,10.]])
    metrics=dict(known_innovations=whitening['innovations'].tolist(),
        known_quadratic=whitening['quadratic'],known_log_determinant=whitening['log_determinant'],
        conditional_mean=prediction['mean'].tolist(),
        conditional_covariance=prediction['covariance'].tolist(),
        parameter_uncertainty_included=False)
    result=dict(version=model.VERSION,passed_checks=passed,software_controls_only=True,
        observed_fit_starts=0,native_predictions=0,archive_records_loaded=0,
        covariance_estimated=False,covariance_calibrated=False,scientific_decision='abstain',
        analytic_examples=metrics)
    HERE.mkdir(parents=True,exist_ok=True)
    (HERE/'summary.json').write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n')
    (HERE/'test-output.txt').write_text(run.stdout)
    readme='''# Shared error model: software checks

**All 35 analytic checks passed.** The proposed covariance calculations are ready
for further development. They have not been fitted to NASA recordings, calibrated
as measurement uncertainty, or substituted into the original Earth-model analysis.

An **IMU (inertial measurement unit)** measures turning and acceleration. The NASA
analysis compares IMU-derived motion with receiver positions. Their remaining errors
are correlated across time and axes. These checks test the mathematics needed to
describe that dependence fairly for all three physical models.

## What was checked

| Control | Independent answer or failure caught |
|---|---|
| White and cross-axis error | Hand-specified covariance blocks, including negative axis correlations; white error does not link different epochs. |
| One or two correlation components | Known exponential covariances at irregular times; positive, ordered time scales. |
| Offset and drift | A prediction subset retains the full-record drift origin and scale rather than restarting drift at the split. |
| Coordinate changes | Different per-epoch rotations and unit scales transform cross-epoch blocks, preserve quadratic cost, and correctly change the density determinant. |
| Whitening | A hand-calculated triangular factor gives innovations [1, 1], quadratic cost 2 and determinant 36. |
| Blocked prediction | Training variance 4, future variance 9 and cross-covariance 2 give predicted residual 1 from training residual 2, with future conditional variance 8. Ignoring the correlation would instead give mean 0 and variance 9. |
| Exact Gaussian moments | Six symmetric, independently generated points reproduce identity whitening and the analytic prediction-error covariance, without Monte Carlo sampling. |
| Difficult matrices and invalid data | A nearly singular positive covariance remains usable; singular/indefinite matrices, invalid times, overlapping splits and malformed inputs are rejected. No hidden jitter, clipping or timestamp repair. |
| Shared specification | Copying inputs prevents later array changes from altering the common error specification. |

The module supports white error, up to two exponentially correlated components,
constant offset and linear drift with cross-axis terms. Matrices are supplied in a
common north/east/up frame; explicit transforms change frames or units. It does not
choose an Earth model or estimate its own covariance from model-specific residuals.

Tiny roundoff asymmetry is averaged only after a relative symmetry check. Component
eigenvalues within a stated machine-roundoff tolerance are retained, not clipped.
Every final covariance must be positive definite. Diagonal equilibration before
Cholesky factorization handles different units without adding error variance.

## What this does not establish

The Gaussian prediction formulas assume the trajectory/residual mean and covariance
parameters are known. A real fit estimates calibration, initial conditions and error
parameters; their uncertainty must be included before predictive coverage is claimed.
The controls do not prove the chosen error family describes the archive, establish
receiver precision, improve solver convergence, or change any model preference.
They make **zero observed fit starts, zero native predictions and zero archive reads**.

## Next step

Develop training-only covariance estimation and an explicit treatment of fitted-
parameter uncertainty, with independent numerical controls. Then freeze the same
error specification for every physical candidate and test blocked predictions under
a separately approved finite observed-data allowance. Preserve all existing results.
The [development plan](../ilvis0-residual-covariance-20261012/ERROR_MODEL_PLAN.md)
sets the scientific constraints. Independent statistical calibration remains separate.

## Reproduce

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python docs/ilvis0-error-model-controls-20261012/build_report.py
```

The qualification is small deterministic matrix arithmetic and input validation;
it does not launch an Earth-model campaign. The report receipt hashes the source,
tests, development plan and generated outputs and records the numerical environment.
'''
    (HERE/'README.md').write_text(readme)
    artifacts=['summary.json','test-output.txt','README.md']
    receipt=dict(version=model.VERSION,numerical_environment=runtime.numerical_environment(),
        observed_fit_starts=0,native_predictions=0,archive_records_loaded=0,
        inputs={str(PLAN):initial[str(PLAN)]},sources={str(p):initial[str(p)] for p in sources},
        artifacts={name:sha(HERE/name) for name in artifacts})
    (HERE/'report-receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print(f'{passed} analytic checks passed; zero observed fits, native predictions or archive reads.')


if __name__=='__main__':build()
