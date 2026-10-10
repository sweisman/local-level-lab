# Can more of the airborne comparisons finish?

**Completed: 10/12 fits converged, compared with 11/12 in the baseline.** The control
still favors globe and then rotation; the diagnostic stretch remains unresolved. This
trial did not improve completion. See the [audited results](RESULTS.md) and the
[saved-fit calibration/adequacy audit](../ilvis0-calibration-audit-20261010/README.md).
The original numerical method and finite scope below are preserved; no further starts are allowed.

This is a small numerical refinement of the completed NASA airborne analysis. An
inertial measurement unit (IMU) records acceleration and angular motion. The analysis
integrates its original increments and compares the predicted track with the embedded
GPS receiver observations under each physical model.

The [completed study](../ilvis0-highspeed-segments-20261008/FINDINGS.md) left 41 of
53 selected stretches unresolved. The [saved-result review](../ilvis0-highspeed-segments-20261008/POST_RUN_REVIEW.md)
found that most unfinished fits exhausted their numerical allowance. This trial tests
whether explicit numerical stability checks make more comparisons finish. It does
not alter the measurements, physical models, nuisance bounds or completed evidence.

## Two matched stretches

| Role | Source | Stretch | Duration | Median ground speed |
|---|---|---|---:|---:|
| Completed control | `ILVIS0_applanix_57300_610_LVIS_38614965.013` | `570b37d23af5e245dd461051` | 7.30 min | 878.06 km/h |
| Unresolved diagnostic | `ILVIS0_applanix_57320_610_LVIS_38614965.013` | `b4e44ddc0f130ecd45674c78` | 7.22 min | 824.94 km/h |

Both contain IMU21 Group-4 records and have the same recorded installation signature.
They are analyzed separately; matching signatures across days do not establish
continuous physical installation. Their original intervals remain exactly as selected
before Earth-model residuals were examined. Selection of this diagnostic pair uses
completion and observable matching, not a desired Earth-model cost difference.

There are **12 approved starts**: three models under two processing assumptions for
each stretch. Each start permits **200 native evaluations**, including initialization,
fresh derivative verification and residual diagnostics. There is **one start per
identity, no retry reserve and no automatic expansion**. An interrupted start counts
and its missing result remains unresolved; restarting the worker does not retry it.

## What changes

The physical prediction, automatic derivatives, receiver covariance, nominal 200 Hz
clock, calibration envelopes and initialization stay the same. Initialization includes
the baseline's force-derived accelerometer gains and zero Earth-rate removal.

The new solver checks three consecutive accepted steps for all of:

- Scaled projected gradient at most `1e-4`, preserving the independent stationarity threshold.
- Relative cost change at most `1e-8`.
- Relative change in the predicted, weighted measurement residuals at most `1e-6`.

The raw gradient fallback is `1e-14`; the parameter-step tolerance remains `1e-11`.
A raw numerical stop is accepted only with independently verified stationarity and
measurement stability. If it stops before stable steps are available, a bounded
linearized correction is checked with an actual native evaluation, within the same
allowance. A correction that materially changes the predicted observations fails that
check. Budget exhaustion never establishes convergence.

The final projected-gradient components, bound signs and Jacobian singular vectors
are saved. They can help identify weak combinations of nuisance parameters. This
does not remove those directions or invent a new rank cutoff. Stable track prediction
does not mean every calibration parameter has been uniquely determined.

Analytic tests cover interior and boundary optima, redundant and poorly conditioned
parameters, a nonlinear known optimum, budget exhaustion and invalid observations.
The source, inputs, environment, method and identities are frozen before observed fits.

## Interpretation and continuation

Compare finished fits, costs, residual consistency and parameter limits against the
saved baseline. Interpret globe/disc first; report rotation only after the required
shape comparisons consistently favor globe. Numerical completion is not model support.
The report will state which model fits better and whether more calculations finish.
It does not assign statistical significance or certify calibration, timing, onboard
corrections or receiver errors. The separate scientific significance gate remains unchanged.

Runtime state is in `data/ilvis0-solver-trial-20261010/status.json`; charged starts and
hashed per-fit results are saved there. The worker publishes a matched report and full
receipts here on completion without refitting. New costs and failures are preserved
whether or not discrimination improves. A changed control result or materially worse
objective requires investigation before considering a larger trial.

Use at most two numerical threads. To launch or resume unfinished, unchanged work:

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python analysis/tests/ilvis0_solver_trial.py --detach
```

The exclusive worker lock is inherited by the detached process, preventing duplicate
numerical workers. Completion prohibits further starts. After completion, use
`--package-only` to regenerate the audited report without any model evaluations.
