# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small analytic training/prediction controls; no archive access or Earth fits."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np

from lll import ilvis0_error_model as covariance, ilvis0_error_training as training, runtime

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
TEST=ROOT/'analysis/tests/test_ilvis0_error_training.py'
PLAN=ROOT/'docs/ilvis0-residual-covariance-20261012/ERROR_MODEL_PLAN.md'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build():
    sources=[Path(__file__).resolve(),Path(training.__file__).resolve(),
        Path(covariance.__file__).resolve(),Path(runtime.__file__).resolve(),TEST]
    initial={str(p):sha(p) for p in sources+[PLAN]}
    env={**os.environ,'PYTHONPATH':str(ROOT/'analysis'),'OPENBLAS_NUM_THREADS':'2',
        'OMP_NUM_THREADS':'2','MKL_NUM_THREADS':'2'}
    result=subprocess.run([sys.executable,'-m','pytest','-q',str(TEST),'--tb=short'],
        cwd=ROOT,env=env,capture_output=True,text=True,timeout=60)
    if result.returncode or result.stderr or '26 passed' not in result.stdout:
        raise RuntimeError('Training/uncertainty controls failed:\n'+result.stdout+result.stderr)
    if any(sha(p)!=expected for p,expected in initial.items()):
        raise ValueError('qualification inputs changed during execution')
    candidates=(('variance1',covariance.Spec(np.eye(3))),('variance4',covariance.Spec(4*np.eye(3))))
    selection=training.select([0.,1.],np.array([-1.,1.]*3),np.ones((6,1)),candidates)
    fitted=training.fit([0.,1.],[2.,4.,6.,4.,6.,8.],np.tile(np.eye(3),(2,1)),candidates[0][1])
    prediction=training.predict(fitted,[2.],np.eye(3))
    metrics=dict(selected_covariance=selection['selected_id'],reml_scores=selection['scores'],
        linear_parameters=fitted.beta.tolist(),prediction_mean=prediction['mean'].tolist(),
        prediction_covariance=prediction['covariance'].tolist(),
        parameter_covariance_contribution=prediction['parameter_covariance_contribution'].tolist())
    out=dict(version=training.VERSION,passed_checks=26,software_controls_only=True,
        observed_fit_starts=0,native_predictions=0,archive_records_loaded=0,
        linear_parameter_uncertainty_checked=True,covariance_parameter_uncertainty_integrated=False,
        active_bounds_supported=False,scientific_decision='abstain',analytic_examples=metrics)
    (HERE/'summary.json').write_text(json.dumps(out,sort_keys=True,indent=2,allow_nan=False)+'\n')
    (HERE/'test-output.txt').write_text(result.stdout)
    receipt=dict(version=training.VERSION,numerical_environment=runtime.numerical_environment(),
        observed_fit_starts=0,native_predictions=0,archive_records_loaded=0,
        sources={str(p):initial[str(p)] for p in sources},inputs={str(PLAN):initial[str(PLAN)]},
        artifacts={name:sha(HERE/name) for name in ('summary.json','test-output.txt','README.md')})
    (HERE/'report-receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print('26 analytic checks passed; zero archive reads, observed fits or native predictions.')


if __name__=='__main__':build()
