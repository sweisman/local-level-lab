# A verified stopping rule before another archive run

## Purpose and implementation

The first pass attempted **all 53 eligible stretches**, with three physical models under
two processing assumptions per stretch. Twelve stretches had every fit complete; 41 did
not. The small follow-up trials diagnose numerical and calibration problems before
applying revisions across that saved population. They do not redefine eligibility or
select favorable gyro observations.

The new candidate is `analysis/lll/ilvis0_solver_verified_stop.py`. It preserves the
unit-scale trial's physical equations, normalized parameter box, staged initialization,
unit scaling in the full stage, SciPy tolerances and finite evaluation cap. All models
use the same stopping policy. It adds two explicitly recorded successful exits:

1. Three consecutive accepted callbacks meet the existing scaled-stationarity,
   cost-change and measurement-step thresholds, followed by a fresh final tangent.
2. A fresh final point passes scaled stationarity and an independently evaluated
   **bounded local correction** confirms measurement stability. This may establish
   numerical completion even when the underlying SciPy search exhausted its allowance.

The original successful-SciPy-stop plus fresh-stationarity exit is retained. A failed
fresh probe stays failed. Budget exhaustion or a small gradient alone never establishes
completion. SciPy's success flag is preserved separately from the candidate's verified
stopping flag. No saved fit is relabeled.

## Bounded correction check

At the fresh point (u), with residual (r) and Jacobian (J), solve the small convex
linearized problem

\[
\min_\delta\|r+J\delta\|^2,\qquad -1-u\leq\delta\leq1-u.
\]

The linear solver must finish. Its predicted cost change must be at most (10^{-8})
relative to the larger cost or one, and its predicted residual-vector change at most

\[
\|J\delta\|/\max(\|r\|,1)\leq10^{-6}.
\]

Then evaluate the actual nonlinear residual and tangent at (u+\delta). Require those
same cost/measurement-step limits and a fresh scaled projected gradient at most (10^{-4}).
A linear prediction alone is insufficient. The probe checks the returned point; it does
not replace it with a newly selected calibration solution.

These are the already published stability tolerances, not thresholds chosen to classify
the failed flat-disc fit. The local bounded solve uses SciPy's BVLS method, tolerance
`1e-10` and at most 100 iterations. It does not integrate observations. The fresh nonlinear
probe does, so it is charged within the same allowance. With a 200-evaluation cap, reserve
four evaluations: one fresh final tangent, one possible fresh probe, and two existing
post-fit prediction sweeps. The main search therefore gets at most 196 tangent evaluations.
No old run gains extra evaluations or retries.

This is first-order numerical qualification, not proof of a global minimum. Nonlinear
stationary points, calibration ambiguity, bound saturation and model inadequacy still need
separate checks. All scientific outputs continue to abstain from calibrated decisions.

## Software qualification

Cheap deterministic tests exercise **24 known-optimum recoveries**: six two-parameter
control families and two 27-parameter families, each from three starting points. They
include interior and boundary optima, redundancy, nonlinear response, gain/offset coupling,
unequal scales and a condition ratio of 50 million. Compare objective and residuals with
independently constructed optima; do not demand unique parameter recovery in weak or
redundant cases.

Additional tests require a fresh probe, reject a misleading linear correction whose
actual nonlinear observations change, preserve unverified failures, enforce box limits,
count every tangent/probe evaluation, preserve staged initialization, and distinguish
verified completion from SciPy success. These checks passed locally. They establish
software behavior; they do not show that the new rule solves the airborne problem.

Reproduce them without airborne fitting:

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=1 ~/venv/bin/python -m pytest -q analysis/tests/test_ilvis0_solver_verified_stop.py analysis/tests/test_ilvis0_solver_diagnosis.py
```

## Next observed comparison and expansion

A separate six-fit freeze should reuse the same control recording, split, models,
processing cases, calibration limits, covariance and initialization. Change only the
solver implementation and its charged stopping verification. One start per identity,
at most 200 evaluations per start, no retries and at most two total numerical threads.
Preserve both earlier six-fit studies. No observed starts are authorized by this page.

Success requires all six fits to complete, retaining all five previously completed
identities without worsening their objectives by more than 0.1%. Report each stop,
probe, physical parameter change, boundary and prediction error, including failures.
A newly verified flat fit is useful only if all models receive the same numerical rule.
The plan must not quietly turn the original unfinished result into a success.

If the matched comparison qualifies, next test the two preselected recordings on
2015-09-24 and 2015-10-22: **two recordings × three models × two processing cases =
12 fits**. These are a small replication check, not a twelve-stretch corpus limit.
Then prepare a versioned run over **all 53 saved eligible stretches**, including the
41 originally unresolved, with its own finite allowance. Do not drop stretches based on
solver outcomes. A full six-fit-per-stretch rerun would require 318 starts; that is a
separate compute decision. Calibration adequacy, uncertainty validation and the free
rotation-field estimator remain separate requirements.
