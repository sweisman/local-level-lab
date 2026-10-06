# A small airline-route pilot

An **IMU (inertial measurement unit)** measures acceleration and turning. This pilot would
test the analysis on simulated IMU readings along an archived Frankfurt–Johannesburg position
track. It compares three corrections using the same generating conditions: the existing wind
correction, the physical wind/airspeed correction, and the physical correction with the optional
mount-movement comparison. The last path still requires agreement with the original exclusion
method before reporting useful evidence.

**The initial three evaluations are complete; all failed before fitting.** They used the
same simulated flight under three corrections. The IMU/GPS relationship was too weak to
establish the aircraft's forward direction. The remaining 15 evaluations have not run and
are not authorized. No model separation, calibration or validation was obtained.

## Initial result

The forward-reference check compares IMU roll with the bank change inferred from GPS course
and speed. All three cases had the same regression gain of 0.0487 and explained fraction
of 0.0123, below the existing requirements of 0.1 and 0.05. The check reported weak roll/bank
correlation, rather than an absence of turn activity. No orientation epoch was unresolved;
57 bins remained for a possible fit. Passing the buffered hand-turn check did not ensure a
usable forward reference.

The existing wind candidate required a measured forward-angle uncertainty; both physical
wind candidates required a three-axis forward reference. None reached the science fit,
envelope or pair profiles. Their 8.14, 8.25 and 6.39 seconds therefore measure failed
preprocessing attempts, not successful-fit cost. Known attempt time totals 22.77 seconds;
the saved run occupies 14,958,617 bytes, including three raw simulated sessions. Two
single-thread workers completed the approved prefix and stopped automatically.

The next useful work is to examine the saved forward-reference calculation and the assumed
trajectory's roll/GPS relationship before proposing another replay. Keep these failures;
do not weaken the reference checks, insert the simulator's known forward axis, or retry
these spent attempts. This result neither tests the airspeed correction nor establishes
failure on an actual flight with its own GPS and IMU measurements.

## What the saved-data investigation established

The bank estimate differentiates GPS course twice. Small errors in course can therefore
overwhelm the roll signal. A diagnostic using the assumed path without GPS noise explains
about 28% of the scalar roll variation, compared with about 1% using the saved noisy GPS.
This comparison isolates a numerical effect; it does not reconstruct measured aircraft motion.

A research-only calculation applies the same 30-second smoothing to both the GPS bank-rate
estimate and the IMU roll readings. It uses complete supported windows, splitting at missing
data or irregular intervals. On these saved sessions it explains about 90% of the horizontal
IMU variation, with gain 0.925, without lowering the existing correlation or gain requirements.
Independent controlled turns recover the known forward direction; GPS noise without roll
does not create a reference. The calculation deliberately supplies **no angle uncertainty or
scientific acceptance**. Uncertainty must account for filtered, correlated data and errors
in the GPS predictor before this can become a fitting method. One development result is not
evidence of calibrated coverage.

The original position interpolation has a second problem: its acceleration can change
abruptly at observation times. Inferring coordinated bank from that acceleration creates
instant bank steps, up to 15.9° here. At the simulated 20 Hz sample rate the assumed scalar
roll reaches about 162°/s. About 93% of scalar roll energy falls within a second of an
interpolation knot. These are artifacts of the assumed path, not observed aircraft turns.

An explicit alternative uses a cubic curve with continuous acceleration inside each supported
block. It preserves every supplied position and height, and the same observation gaps. On
this window the largest scalar roll rate is below 0.34°/s; the finite one-sided knot check
is below 0.00031°. This removes the bank-step artifact, but its endpoint curvature and motion
between fixes are still assumptions. It may overshoot on other tracks and must be reviewed.
The original interpolation remains the default for historical specifications; the alternative
has its own version and trajectory hash. No flight has been generated from it.

The next implementation step is an uncertainty-aware matched forward-reference method,
with controlled tests of GPS error, missing data and real turns. Then a separately budgeted,
freshly frozen pilot can compare the smoother route through the full pipeline. Do not resume
the old plan after scientific-source changes or use these diagnostics as replacement winners.

That method is subsequently implemented as an opt-in research candidate, with a joint GPS/IMU
covariance and tests including continuous small aircraft corrections. The saved-data
`forward-uncertainty-review.json` reports angle sigma 0.010193 radians (about 0.58°), while
preserving all original failures and recording no science fit. The [fresh matched pilot](../matched-airline-pilot-20261006/README.md)
uses a new source freeze and seed; it remains unrun and requires a new compute budget.

## What the assumption review found

Five archived route windows were reviewed using the already declared smooth-path interpolation.
They contain sparse public position observations; frequent GPS and IMU readings remain simulated
assumptions. Reported height and clock references are unconfirmed. These calculations do not
measure GPS accuracy or establish what happened between observations.

The existing 20/40/60-minute IMU-turn control passes the two-minute buffered assumed-motion
check on Frankfurt–Johannesburg and Seattle–Keflavik. It fails on the selected windows for the
other three routes. Those failures remain recorded; the times and motion limits were not
adjusted to obtain a pass. Even a passing assumed-path check does not certify the reconstructed
orientation or a usable scientific recording.

The physical correction imposes consistency between the wind vector, ground velocity and a
slowly varying airspeed. Its fixed constraint width is 2 m/s and its knots are 15 minutes apart.
There is no independent airspeed or aircraft-heading measurement. A constrained fit therefore
depends on these smoothness assumptions, rather than deriving airspeed uniquely from GPS.

For a separate diagnostic, prescribed wind was subtracted from the assumed ground path to
calculate its implied airspeed. Values sampled at 15-minute knots were interpolated without
optimization. On Frankfurt–Johannesburg, the absolute mismatch has a median of 2.95 m/s,
95th percentile of 11.41 m/s and maximum of 20.68 m/s; 79.7% of sampled points are within 6 m/s.
The other four windows have maximum mismatches of about 23–49 m/s. This calculation spans
supported path points, including intervals that later preprocessing might exclude. It is not
the optimal airspeed spline, a fitted model residual, or proof that the physical correction fails.
It shows why assumed interpolation roughness and airspeed smoothness need a matched test.

All 65 frozen wind/airspeed design states were also checked against their speed constraint.
None remains within 6 m/s at every sampled point on any of these assumed paths. The finite
grid intentionally includes independent wind/TAS corners and off-constraint combinations;
that result is not an identifiability score. No state was removed, tolerance widened, nuisance
model changed or science cutoff relaxed. A future review should decide whether a geometry-only
envelope over jointly credible states better represents the experiment, using evidence beyond
which states produce attractive model separation.

## The concrete proposal

The frozen proposal uses the supplied public LH572 FRA–JNB window in simulated-frequent-GPS
mode. It keeps the current 20/40/60-minute control, fresh development seed 600900, three model
truths and two scenarios: wind with mixed IMU bias, and wind with bias, correlated noise and
temperature effects. The three candidates make **18 evaluations of six generating conditions**.
They share RNG streams for matched comparisons and are not 18 independent null draws.

The initial completed stage is **three evaluations** of the same rotating-globe/wind-plus-bias
condition, one per candidate. Its purpose is to measure current runtime, diagnostic storage,
exclusions, parameter-boundary behavior, forward-axis uncertainty and available model-pair
information. The remaining 15 evaluations need a subsequent budget decision using those
measurements. Zero bootstrap keeps this a development diagnostic; it cannot establish a rare
error rate, justify a winner or replace calibration and independent validation.

Use at most two worker processes, each with one numerical thread. Historical 7–12-second flight
times are not a quote for the larger nuisance envelope and two-path fits. Successful-fit runtime
and storage remain unmeasured. No schedule search is included. True mount-slip controls, other routes,
the original sparse-fix lane, larger wind/airspeed departures and complete nonlinear bootstrap
remain separately scoped follow-ups. In particular, the mount candidate cannot be assessed
for slip detection merely from wind/no-creep cases.

## Frozen technical record and reproduction

`plan.json` is a `sharded-flight-campaign-1` plan with source/configuration/policy/one-thread
environment and exact candidate jobs frozen. `assumption-review.json` records every reviewed
route, input hashes, turn-mask failures, all 65 speed-state diagnostics, task IDs and the
provisional assumptions. Their original preparation declarations remain immutable; subsequent
approval covered only the first three evaluations, now spent. `run/` preserves their journals,
raw sessions, preprocessing arrays and partial export. `processing-review.json` records the
saved-data forward-reference audit from `analysis/tests/audit_airline_pilot.py`; it generated
no flights, science fits, SVD calculations or search. The partial export is not holdout evidence.
Preparation helper: `analysis/tests/prepare_airline_pilot.py`; six controlled checks are in
`analysis/tests/test_airline_pilot_preparation.py` and passed in 1.07 seconds. They fail if
preparation invokes a flight fit or SVD, exercise smooth/jittered paths, verify the matched
prefix and reject an unsafe selected schedule. The preparation itself took less than a second.

The completed pilot's scientific source was
`d5d63a6eec604ac2ba02cb39648767a914841f3c05bb8790eeb1ef442f95cb42`.
The required worker environment hash is
`20ef393862e7723ba90e825b625826081cde501e4d9c944f2dbff29526ebdd69`.
Plan hash: `74b7de930a28daeb5dc56884f1baefc990a32c1bcc68b285ea33ef6c4a75bfe7`.
The preparation script and archived inputs have their own hashes inside the frozen configuration.
Earlier core/wind proposals remain historical and were not overwritten.

That source hash identifies the completed pilot. The explicit smoother trajectory extension
subsequently changed the current implementation hash to
`3b42547d5a2ffa2a2ef5d975382b4b1b2b0a762fe831493d40cb1b7f469cb682`;
the old plan is now historical and cannot run under this source. Preparation/diagnostic helpers:
`audit_roll_proxy.py`, `forward_smoothing_diagnostic.py` and `prepare_smooth_route.py` in
`analysis/tests/`. Controlled checks for the new helpers and trajectory compatibility,
the existing core pipeline, processing audit and original preparation passed **51 tests in
2.39 seconds**. This is focused software evidence, not a full-suite or campaign result.

`roll-proxy-review.json` records the scalar cause audit. `matched-smoothing-review.json`
preserves the first diagnostic; `matched-smoothing-support-review.json` is the subsequent
gap-support-hardened result, using 4,187 windows. `smooth-trajectory.json` declares the explicit
alternative; `smooth-route-review.json` records its geometry-only comparison. Original failed
flight records, plan and preprocessing audit remain intact.

The initial authorized run used this command with `--detach`; its budget is now exhausted.
This is a reproduction record, not authorization to generate new attempts:

```sh
/home/sweisman/venv/bin/python analysis/tests/sharded_campaign.py run docs/airline-pilot-preparation-20261006/plan.json --output docs/airline-pilot-preparation-20261006/run --workers 2 --attempt-limit 3
```

An explicit detached launch can survive terminal/chat disconnection, following the
[runner instructions](../sharded-campaigns-20261006/README.md). Codex must launch outside its
per-command sandbox so an authorized child survives command completion. The output `run/`
now exists and its status is `budget_complete`, with three preserved failures. Do not use
`--attempt-limit 18` without approval
of the additional work. No runtime ceiling is encoded in this proposal; a strict wall-time
budget would need an execution deadline before launch, not an invented runtime estimate.
