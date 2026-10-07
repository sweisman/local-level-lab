# What remains in the development plan

The main implementation work from the review is present. The remaining task is demonstrating
that useful flight geometry survives realistic instrument and aircraft uncertainties, then
calibrating and independently validating the resulting decisions. Implemented software and
successful numerical fits do not establish that the physical models can be distinguished.

| Review item | Present in the software | What still needs evidence |
|---|---|---|
| Nuisance envelope | Design checks vary crab, wind, forward angle and mount epochs across model anchors. | Show that a selected geometry survives the declared envelope and complete preprocessing. The finite grid is not a guarantee over every nuisance trajectory. |
| Real airline trajectories | Replay input and five prepared windows exist; two supplied tracks were unsuitable. Matched pilot prefixes have run. | A useful route/window and IMU-turn schedule. The pilots so far yield no eligible contrasts; the full proposed comparisons remain unfinished. |
| Turns away from maneuvers | Buffered aircraft-motion checks guard planned IMU turns. | A schedule that passes these checks and preserves model separation on an actual route. |
| Physical wind and airspeed | An optional north/east wind and true-airspeed candidate is integrated. | Justify its assumptions and conditional speed information, then compare it with the broader wind candidate. Choosing the more restrictive candidate merely because it passes is insufficient. |
| Magnetic ambiguity | Optional piecewise mount-yaw modeling retains ambiguous data and requires agreement with the exclusion path. | Independent calibration of both paths and evidence for genuine mount movement versus aircraft crab. The default remains exclusion. |
| Combined adversaries | Composable wind and mixed sensor-bias scenarios are implemented and used in pilot work. | Matched comparisons over the final nuisance domain, including relevant correlated-noise and thermal combinations. |
| Pairwise evidence | Direct pair-specific profiles, abstention, pooling and globe/disc preferences are implemented. | Fresh pairwise calibration, pooled-domain validation and a separate error budget for the composite globe/disc rule. Historical development preferences are uncalibrated. |
| Operational domain | Versioned observable domains bind primary/pairwise eligibility and threshold artifacts. | Select and validate a useful domain, with actual threshold files. Real-upload empirical decisions remain refused. |
| Parallel campaigns | Deterministic, journaled two-worker execution and checked merging are implemented and exercised. | A new bounded budget for further simulations and a final frozen scientific configuration. Each worker uses one numerical thread. |

Recent processing work also addresses nuisance-rank scaling, forward-reference noise/motion
handling and finite-run course unwrapping across gaps. Actual forward-reference uncertainty
and its statistical coverage still need evidence; software fixtures do not establish it.

The immediate order is:

1. Continue inexpensive route/window/turn screening under the unchanged nuisance space.
   Evaluate rotation and globe/disc questions separately. Seek an actual observed route,
   not only a counterfactual direction control.
2. For promising controls, review the finite envelope assumptions and obtain a separately
   bounded budget for complete-envelope evaluation and matched full-pipeline replay.
   Preserve every failure and abstention. Do not rerun spent attempts to improve acceptance.
3. Decode the supplied airborne IMU using a documented physical format, and qualify actual
   devices when available. These are separate evidence sources: the NASA instrument cannot
   establish consumer-device drift or accuracy.
4. Once a useful domain is demonstrated, freeze source, configuration, eligibility policy,
   observable domain and numerical environment. Preregister primary, pairwise, pooled and
   composite-shape error budgets where applicable.
5. Run fresh calibration, freeze its actual decision artifacts, then run independent
   validation and assess the simultaneous exact bounds. Production use follows a reviewed
   policy revision, not a development preference.

All previously authorized simulation attempts have been spent; no worker is being launched
by this continuation. Earlier calibration costs and prospective execution freezes are stale.
No usable fully validated protocol or empirical Earth-model result has yet been demonstrated.

## Latest inexpensive check

A fixed reversed traversal of the preserved 120-minute AUH–ORD path, with six IMU turns,
previously passed a nominal globe/disc design check under the physical wind candidate.
The bounded follow-up evaluated 30 states from the existing registered envelope in about
0.10 seconds. These include zero wind and some individual wind drifts, all three model
anchors for completed state groups, and forward-angle offsets of 0° and ±15°.
Both globe/disc retained fractions remained above the threshold in that subset: minima
0.403480 and 0.431011 against 0.312250. The evaluation cap stopped partway through the grid.
This found no counterexample; it did not complete or certify the envelope. Other wind
corners, airspeed levels, mount epochs and noise states remain unchecked here.

The broader wind candidate already fails the nominal check on this same reversed path.
The reversed traversal is not a measured eastbound flight, and no sensor synthesis, fitting,
bootstrap or calibrated decision was performed. Thus this remains a design clue, not a
protocol recommendation. The recorded states and input/helper hashes are preserved in
`direction-envelope-counterexample.json`, produced by
`analysis/tests/check_direction_counterexamples.py`.

The [airborne sample notes](airborne-sample-ilvis0/README.md) and
[format follow-up](FORMAT_FOLLOWUP.md) describe the separate real-data step.

## Whole-route two-hour screen

The earlier longer-window search extended only anchors that already had promising
75-minute geometry. A separate check now samples two-hour windows every 15 minutes across
all seven recorded tracks, regardless of those earlier outcomes. It uses three fixed
patterns: no IMU turns; turns at minutes 25, 50 and 85; and turns at minutes 10, 30, 50,
70, 90 and 110. Coverage, aircraft-motion buffers, duration and heading rules are unchanged.

Of 176 overlapping windows, 130 failed observed coverage and one lacked the required height
information. The remaining 45 windows received motion/heading screening. Seven window-and-
pattern combinations passed: six on Abu Dhabi–Chicago and one on Chicago–Los Angeles.
No eastbound combination passed the heading requirement on this grid. None of the seven
passing controls preserved any model contrast above the retention threshold under either
wind candidate, even at nominal nuisance settings. These SVD checks use all three model
anchors, dynamic sensor bias, forward-angle uncertainty, zero wind/angle, nominal true
airspeed of 250 m/s and a fixed 6°/hour noise assumption.

The complete check took 1.80 seconds and used no simulated flight attempts. Six existing
motion-screen and direction-control fixtures passed in 0.45 seconds. Results and input/helper
hashes are preserved in `long-route-window-screen.json`; the reproducible helper is
`analysis/tests/screen_long_route_windows.py`. This coarse search is not exhaustive and
does not establish impossibility. Other starts, lengths and safe turn timings remain open.
No expensive replay, full-envelope calculation, calibration or protocol promotion followed.

The continuation checked three-/four-hour windows independently of the earlier anchors.
The [longer-route review](EXTENDED_ROUTE_REVIEW.md) records 277 additional windows,
250 coverage failures, 27 motion-screened windows and ten preliminary passing combinations.
None passed any nominal model contrast; no four-hour combination passed the preliminary
screen. Six patterns per duration include shifted central six-turn timings, with all
existing schedule and maneuver rules preserved. Runtime was 2.65 seconds; six existing
motion/direction checks passed in 0.44 seconds. No flights were simulated.
The helper is `analysis/tests/screen_extended_route_controls.py`; its output is
`extended-route-controls.json`. The invalid initial timing diagnostic is preserved separately
and excluded from scientific conclusions. These results do not exhaust possible schedules.

## Safe timing search and partial evidence

The [turn-timing review](TURN_TIMING_REVIEW.md) records the next bounded search:
88 safe schedules on the 11 previously preliminary-passing windows, with no passes across
both wind candidates. Sixteen individual schedule/pair comparisons passed nominally under
the physical wind candidate alone. Small registered-state checks disproved five; eleven
remain unresolved. No full-envelope claim, noisy replay or empirical decision follows.

The strongest surviving stationary-globe/disc partial control is frozen in
`observed-pair-envelope-plan.json`: actual ORD–LAX elapsed seconds3600–10800,
turns5/15/30/40/90minutes and the physical wind candidate. Its complete registered envelope
was authorized and completed on 2026-10-07: all15,210states in29.70seconds, one numerical
thread, under the120-second cap. The direct-pair retention is at least0.365100 against
0.312250; this partial comparison passes the finite grid. The global rank is1 throughout.
Rotation passes narrowly in the direct-pair calculation but fails after the global rank
cutoff; rotating globe versus disc fails under either calculation. The completed result is
`observed-pair-envelope-result.json`. No flight was simulated and no threshold calibrated.

Next: prepare and separately budget matched full-pipeline replay of this fixed control across
the three truths, combined wind/sensor drift and both wind candidates. Supplied design axes
must be replaced by actually recovered axes. Broad wind already fails nominally, so the
physical candidate's assumptions need scientific justification even if replay succeeds.
The existing flight-attempt allowances remain spent; this one-envelope compute approval is
also complete. Do not rerun it or start another envelope/replay without the required budget.

## Completed matched full-pipeline replay — 2026-10-07

The later user authorization covered six development attempts: three truths × two wind
candidates, shared fresh seed600910 and combined wind/bias_mixed. The frozen control is
unchanged. All six analyses completed and converged in335.20wallseconds, with 99cruise
minutes and adequate headings. Orientation was actually recovered from simulated readings.
The two candidates received independently verified identical fitter inputs within each truth.
Both rotation and stationary-globe/disc pairwise gates pass in all six cases; rotating-globe/
disc fails, and the complete three-model gate remains excluded. All decisions abstain:
zero bootstrap, no empirical thresholds, no calibrated winner or error-rate claim.

The [replay summary](../observed-pair-replay-20261007/SUMMARY.md) and its frozen evidence
record the new limit: residual-based gyro scales are about38.3°/hour rather than the3–6°/hour
planning assumption. Stationary-globe/disc profile standard errors are0.62–0.64 on endpoints
one unit apart. The saved-data decomposition is now complete: aircraft-motion mismatch is
39.63°/hour RMS, sensor/calibration remainder3.86–3.93°/hour, and the false tilt correction
from treating specific force as gravity is38.12°/hour. Prescribed true-plumb substitution,
with saved fit parameters unchanged, leaves about12°/hour. These correlated components
cannot be added as independent variances. No fit, new flight or decision was produced.
Next develop an observed-data acceleration-aware orientation/motion correction and test its
uncertainty before a bootstrap/power pilot or large calibration. True simulator attitude
must stay diagnostic-only. Do not attribute these scales to real-device noise. The six attempts are spent;
there are no active workers or authorization for additional flights, calibration or promotion.

The [observed-data acceleration prototype](../acceleration-motion-20261007/README.md) is
now implemented outside production. Independent motion fixtures and saved-data checks pass
(11focused tests). On the same85supported minutes, residualRMS falls33.75–33.89to11.12–11.20dph
with saved parameters held fixed. All93sensitivity states complete;83minutes have common
support. Their residual range9.6–37.3dph shows that wind/orientation coupling remains material.
GPS/IMU uncertainty propagation is provisional and assumes independent errors. No new flight,
optimizer, eligibility change or decision was produced. Next couple observed acceleration
and orientation to the research wind/forward nuisance parameters and verify their joint
uncertainty and remaining motion error before any separately scoped refit/calibration.

The coupled prediction and bounded saved-data refits are now complete. Corpus:
[joint-motion study](../joint-acceleration-motion-20261007/README.md). The correction varies
with the fitted wind/forward parameters and six coherent error modes; its Jacobian/covariance
include those paths. Fixed support83minutes. All24optimizations converge and nest; no boundary
flags or repairs. ResidualRMS7.92–8.57dph, summed optimizer309.86s. Sixteen focused checks pass;
checkpoint hashes and a zero-extra-call resume are verified. No new flight, bootstrap,
calibration, eligibility change or model decision. Weights/error priors remain provisional.
The [saved-data filtering/covariance check](../matched-measurement-motion-20261007/README.md)
is now complete: identical additional filtering of observation and full prediction leaves
79common minutes, reducing residualRMS7.85–8.32to7.08–7.48dph. Slow-prediction interpolation
changes only0.026–0.040dph. An explicit gyro covariance propagates filter overlap and axis
rotations; independent-second marginal scale~3.53dph is provisional and includes motion.
Residual adjacent-minute correlation reaches−0.61; fitted-residual correlation does not
identify a noise source or prove significance. All six cases and checks are preserved;
21focused tests pass,0optimizercalls/newflights,0activeworkers.

The [continuous-equation/shared-error check](../continuous-measurement-motion-20261007/README.md)
is now complete. All terms are evaluated at GPS timestamps; no slow-term interpolation.
Six saved free-fit states,79common minutes, residualRMS7.0763–7.4782dph. Shared GPS/paired
IMU covariance gives fixed-parameter sigma11.2533–11.2722dph under independent-second
assumptions, about90% of variance from GPS. Local old-weight penalized fit response
preserves GPS/physical-speed-constraint cross covariance; residualsigma11.1343–11.1603dph.
This is conditional sampling propagation at saved states, not a fit or validated coverage.
Eight new tests,29focused total; independent full-input derivative and least-squares
response checks pass. Six checkpointed evaluations,0optimizer/newflight,0activeworkers;
completed-scope resume skips all6.

The [temporal covariance study](../temporal-measurement-covariance-20261007/README.md)
is complete:6saved cases×36GPS/IMU persistence combinations,216scenarios. Durations0/1/5/15/
60/300s, exponential elapsed-time kernel, fixed marginal scales/79minutes. Sensor-axis IMU
roots preserve mount rotations and shared errors. Predicted fixed-state sigma11.2533–
42.3085dph; local fit-response residualsigma11.1343–40.6480dph. Worst residual scale uses
GPS15s/IMU300s in every case. This grid is assumed sensitivity, not a credible-domain bound
or characterized physical covariance. Baseline recovery, dense-kernel, PSD and all216
response summaries verified;34focused tests pass,67.803summed seconds,0optimizer/newflight/
activeworkers. Resume skipsall6. Next implement/verify a covariance-aware research objective
with shared GPS auxiliary errors before separately defining any further finite refit scope.

The [frozen-covariance objective study](../covariance-measurement-objective-20261007/README.md)
is now complete:216saved-state evaluations, full joint whitening, matching gyro/auxiliary
signs, fixed matrices, log determinant and deterministic penalties. Singular matrices
fail without jitter/clipping. A second216comparison preserves the existing2m/s physical
wind discrepancy as explicit auxiliary covariance. Measurement-only physical-wind
quadratics27,718–598,005 shrink to167–336with that registered allowance; broad-wind
controls unchanged. These old-state objectives are not calibrated fit statistics.
44focused tests, independent matrix/directional/response checks pass;54.164+7.093summed
seconds,0optimizer/newflight/activeworkers; completed resumes skip allcases.

The [saved-recording GLS comparison](../covariance-refits-20261007/README.md) was separately
authorized on October 7 and is complete. Six saved cases×4fixed correlation pairs×
(free+3fixed)=96primaryfits,≤120starts including predefined single nesting repairs and
interruptions, max_nfev200. No bootstrap/newflights/decisions. A source/input/environment
freeze, synced per-fit archives and append-only journal support safe continuation.
Six cases share three simulated recordings, not six independent flights. All96fits
converge; all24comparisons nest;0repairs/interruption/failures/boundary or1%-near-bound
fits. Optimizer1732.595s; about30.5minutes launch-to-completion, one numerical thread,
no active worker. Free residualRMS4.4711–9.8778dph. Independent residual/objective/
full-equation direction checks, covariance/support identity and start/fit checkpoint
audits pass;17focused checks. Resume skips all24comparisons with no additional starts.
Injected model has the lowest fixed objective for every assumption/candidate, but
differences shrink substantially with longer error persistence. Local data-only
contrast retention is23.5–52.4%rotation/still,4.0–14.3%rotation/disc,31.7–64.3%still/disc.
These free-state diagnostics apply no gate or calibrated threshold. Weak rotation/disc
geometry remains; covariance persistence/reference/calibration coverage remains unmeasured.
Next characterize hardware/GPS persistence and validate the motion correction, then
define a defensible research-candidate covariance domain and informative protocol.
Fresh calibration and independent validation follow; no further campaign is authorized.
