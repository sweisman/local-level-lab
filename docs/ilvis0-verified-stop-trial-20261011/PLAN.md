# Matched verified-stopping trial

## Scientific comparison

This proposal tests the candidate described in the
[stopping plan](../ilvis0-solver-diagnosis-20261011/STOPPING_PLAN.md). It authorizes no
numerical starts until its finite allowance is explicitly approved.

Reuse recording `ILVIS0_applanix_57300_610_LVIS_38614965.013`, IMU type 21,
2015-10-05 12:45:50–12:53:08 UTC, median ground speed 878.06 km/h. Preserve the
same 292 training epochs, 147 prediction epochs, continuous propagation without GPS
resets, physical models, both processing cases, all physical bounds, packet-header
clock, covariance and training-only staged initialization. The split is retrospective;
this is numerical development, not independent confirmation.

Change only the solver's charged stopping verification, as specified by
`analysis/lll/ilvis0_solver_verified_stop.py`. Unit scaling in the full stage remains;
initialization uses Jacobian scaling. The fresh bounded probe reserves an evaluation
inside the existing cap. Save SciPy status, verified stopping status, probe predictions
and actual checks, gradients, callback history, singular vectors, active bounds and
prediction errors. All candidates receive identical rules.

## Qualification

All six fits must complete. Preserve the five previously completed identities without
worsening their training objectives by more than 0.1%; compare against the original
prediction trial and the completed fixed-scale trial. Keep all failures. Report physical
parameter and boundary changes separately from numerical success. Do not widen bounds,
alter covariance, change initialization from prediction outcomes, or promote a result
because it favors a model. Shape comes first; rotation remains withheld unless both
processing cases resolve shape in favor of globe. Statistical decisions continue to abstain.

The candidate passed 24 independently constructed known-optimum recoveries and additional
false-stop, fresh-evaluation, boundary, staged-initialization and budget tests. They do not
establish convergence on this airborne recording or a global minimum.

## Finite allowance and estimated cost

Proposed allowance: **six starts, one per identity, 200 evaluations per start, no retries**,
one worker with at most two total numerical threads. The 200 cap includes up to 196 main
tangent evaluations, a fresh final tangent, one possible fresh stability probe, and the
two existing post-fit prediction sweeps. Unused reserved evaluations do not increase the
main-search cap. Interrupted starts stay charged; never resume a completed study.

The previous trial used 749 evaluations and 33.4 minutes of fitting/diagnostics. Applying
its average measured cost to the 1,200-evaluation ceiling gives about **54 minutes**;
its slowest fit's measured rate gives about **62 minutes**. Allow roughly **55–65 minutes**
plus setup/publication if the fits use their allowances. This is an estimate, not a guarantee.

Preparation freezes source/input/environment hashes and the existing split with zero starts:

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python analysis/tests/ilvis0_verified_stop_trial.py --prepare-only
```

After approval only, use the same environment with `--detach`. Its exclusive lock,
append-only journal and atomic hashed outputs follow the tested existing worker. The
adapter and original reused worker are both frozen. Keep all original studies unchanged.
No recording-replication or full-corpus starts follow automatically.
