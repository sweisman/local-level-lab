# Joint Z-axis calibration profiles: staged development plan

**Prepared scope, not authorized execution.** The completed studies are frozen.
The [saved-result audit](README.md) found that the revised integration left all six
Z gain/offset solutions at the same limits and completed only four fits. Both
unfinished zero-field globe fits fail stationarity by more than fifty times.
This is not a reason to retry those fits or replace the archive's solver.

An IMU (inertial measurement unit) measures turning and acceleration. Here, gyro
gain changes the scale of its measured turning; offset adds a constant correction.
A joint profile fixes both corrections to specified values, then fits all other
permitted parameters. It can show whether many correction combinations fit almost
equally well, or whether a model consistently requires an extreme correction.
It does not measure time-varying instrument drift.

## First stage: one complete reference, one clock, one processing case

Reuse the full 438-second selected stretch `570b37d23af5e245dd461051` from
`ILVIS0_applanix_57300_610_LVIS_38614965.013`, IMU record type 21. Its median
ground speed is 878.06 km/h and minimum is 859.55 km/h. Preserve the saved selection,
source hash, integer increments, receiver observations and extraction provenance.
Do not select or shorten a stretch using gyro residuals.

Use the original integration and packet-header intervals from the completed
six-fit clock reference. This isolates calibration in a method that completed the
control; it does not establish the proprietary increment convention. The revised
integration is a later sensitivity stage, not the default for these profiles.

First use `bias1_unsubtracted`: zero upstream field removal, with the original
±1°/hour constant gyro-offset limits and every other physical bound unchanged.
These limits remain sensitivity assumptions, not measured per-unit limits.

| Fixed Z gain | Fixed Z offset, degrees/hour |
|---:|---|
| −2% | −1, 0, +1 |
| 0% | −1, 0, +1 |
| +2% | −1, 0, +1 |

Run the specified-field globe, zero-field globe and stationary disc at **all nine
coordinates**: 27 identities. Removing two fixed coordinates leaves 24 free
parameters in this non-removal case. The same reduced coordinates and bounds
must be used for every model. Keep the frozen solver, initialization stages,
receiver covariance, mounting transformation and observation metric.

Begin each point at zero in the other normalized coordinates, with its two fixed
coordinates already inserted. Do not warm-start from the favored model, a previous
grid point or the unrestricted fits. Use the frozen initialization stages. Grid
order is gain, then offset, then the three models; order grants no adaptive retries.

The unrestricted clock fits are comparison references, not fixed-profile starts.
Even when an unrestricted optimum is at a grid corner, it does not replace the
scheduled fit. A profile result worse than that feasible reference at the same
corner flags incomplete optimization; it does not invalidate the saved reference.

## Finite cost and execution requirements

Request **27 starts × 200 native sweeps = at most 5,400 sweeps**, one start per
identity, no retries. Count failed and interrupted passes and any final diagnostic
predictions. Reserve two final prediction passes within the 200 limit; never add
untracked evaluations to obtain a report. The proposed identity ledger is generated
by `lll.ilvis0_integration_audit.profile_scope()` and saved in `profile-scope.json`.
Its authorized-start count is zero.

At the measured roughly 3.8–4.3 seconds per pass, full budgets take approximately
6–7 serial hours. This estimate is not a larger allowance. One worker may use
two numerical threads total. Do not run another numerical study concurrently.

Before requesting launch approval, implement and test a separate profile worker.
Test fixed-coordinate expansion, unchanged physical decoding, reduced Jacobian
columns, feasible-bound stationarity, known-optimum controls and native accounting.
Do not edit frozen fitter or kernel sources to freeze the two coordinates. Tests
must show that the solver cannot move either fixed value, including at ±1 normalized
coordinates, and that its final diagnostics describe only free feasible directions.

Seal sources, tests, this plan, identity ledger, original reference, selection,
conversion, compiler/kernel hashes and numerical environment in a new development
manifest. Preparation and packaging must not extract or integrate original data.
Observed extraction occurs only during an authorized run. Changed freezes require
new identities and consent; no unused completed-study budget transfers here.

Hold an exclusive shared lock; journal and fsync each charged start before execution.
Save hashed results atomically. A charged identity without a verified result remains
an interrupted failure. Resume only uncharged identities in an unchanged unfinished
freeze; completion prohibits resume. A detached worker must survive the command
sandbox, publish on completion and preserve its journal and failures.

## Diagnostics and interpretation

Save cost, receiver-coordinate errors, convergence, stationarity, elapsed time,
sweep counts, all fixed/free physical parameters and free active bounds. Capture
the full and free gradients, scaled/projected free gradient, singular values and
right singular vectors from the already counted final tangent pass. Record vector
coordinate order and distinguish fixed Z coordinates from free active bounds.
Step-history capture must not change solver behavior; if unavailable, say so.

Plot each model's absolute achieved cost over the feasible gain/offset rectangle,
alongside within-model cost differences and the unrestricted solution. Keep separate
panels and a common absolute scale for comparisons. Do not normalize away a model's
poor absolute fit. Annotate all nine coordinates and convergence status. Unfinished
points are upper bounds on their unknown optimized costs and must not form completed
contours. A 3 × 3 grid cannot resolve a narrow valley or prove global optimality.
Cost contours are not confidence regions before uncertainty calibration.

This stage evaluates one processing case on one recording. It cannot establish
robustness across both processing assumptions, clocks, integrations or instruments.
Interpret geometry first. Compare background fields only after a complete matched
globe result, and describe any such comparison as limited to this diagnostic stage.
All scientific decision flags remain abstentions. Neither field model identifies
the field's cause or tests the solar/sidereal rate difference.

After review, separately scope the profiled-removal case, nominal clock and revised
integration if the first grid is informative. The full two-clock/two-processing
3 × 3 grid would require 108 starts before integration variants. No later stage,
recording replication or corpus rerun is implicit in the first-stage plan.
