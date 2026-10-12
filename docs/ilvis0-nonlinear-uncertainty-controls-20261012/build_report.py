# SPDX-License-Identifier: AGPL-3.0-or-later
"""Deterministic toy uncertainty checks; no NASA data or numerical Earth fits."""
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
from scipy.integrate import quad
from scipy.special import ndtr
from scipy.stats import chi2

from lll import ilvis0_uncertainty_geometry as geometry, ilvis0_error_model as error, runtime

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
TEST=ROOT/'analysis/tests/test_ilvis0_uncertainty_geometry.py'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def boundary_control():
    # Independent observation law: Y~N(0,1), constrained estimate theta in [0,10].
    # Its exact optimum is min(10,max(0,Y)); not a Gaussian centered at its mode.
    density=lambda z:math.exp(-z*z/2)/math.sqrt(2*math.pi)
    tail=quad(density,10.,np.inf,epsabs=1e-13)[0]
    mean=quad(lambda z:z*density(z),0.,10.,epsabs=1e-13)[0]+10*tail
    second=quad(lambda z:z*z*density(z),0.,10.,epsabs=1e-13)[0]+100*tail
    variance=second-mean*mean
    np.testing.assert_allclose([mean,variance],[1/math.sqrt(2*math.pi),.5-1/(2*math.pi)],atol=1e-12)
    threshold=float(chi2.ppf(.95,1));boundary_coverage=float(ndtr(math.sqrt(threshold)))
    if abs(boundary_coverage-.975)>1e-12:raise ValueError('boundary likelihood coverage control failed')
    return dict(estimated_parameter_mean=mean,estimated_parameter_variance=variance,
        probability_estimate_equals_lower_bound=.5,
        unconstrained_gaussian_variance=1.,incorrect_fixed_bound_variance=0.,
        nominal_interior_chi_square_95_threshold=threshold,
        coverage_at_boundary_for_that_threshold=boundary_coverage)


def build():
    sources=[Path(__file__).resolve(),TEST,Path(geometry.__file__).resolve(),
        Path(error.__file__).resolve(),Path(runtime.__file__).resolve()]
    initial={str(p):sha(p) for p in sources}
    result=subprocess.run([sys.executable,'-m','pytest','-q',str(TEST),'--tb=short'],cwd=ROOT,
        env={**os.environ,'PYTHONPATH':str(ROOT/'analysis'),'OPENBLAS_NUM_THREADS':'2',
            'OMP_NUM_THREADS':'2','MKL_NUM_THREADS':'2'},capture_output=True,text=True,timeout=60)
    if result.returncode or result.stderr or '25 passed' not in result.stdout:
        raise RuntimeError('Nonlinear uncertainty controls failed:\n'+result.stdout+result.stderr)
    control=boundary_control()
    if any(sha(p)!=expected for p,expected in initial.items()):raise ValueError('qualification source changed')
    report=dict(version=geometry.VERSION,passed_geometry_checks=25,boundary_distribution_control_passed=True,
        software_controls_only=True,archive_records_loaded=0,observed_fit_starts=0,native_predictions=0,
        nonlinear_NASA_uncertainty_qualified=False,confidence_calibrated=False,scientific_decision='abstain',
        boundary_example=control)
    (HERE/'summary.json').write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+'\n')
    (HERE/'test-output.txt').write_text(result.stdout)
    receipt=dict(version=geometry.VERSION,numerical_environment=runtime.numerical_environment(),
        archive_records_loaded=0,observed_fit_starts=0,native_predictions=0,sources=initial,
        artifacts={name:sha(HERE/name) for name in ('summary.json','test-output.txt','README.md','NEXT_PLAN.md')})
    (HERE/'report-receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print('25 geometry checks and independent boundary-distribution control passed; no NASA fits or reads.')


if __name__=='__main__':build()
