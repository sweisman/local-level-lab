# Learning calibration before predicting the later flight

## Question

The [gravity-mechanization controls](../esa-gravity-controls/README.md) pass all
48 cases when initial state and calibration are known. Can the shared pipeline
instead estimate those quantities from earlier receiver positions and predict
unused later positions on a twenty-minute climbing track?

This is a generated-data qualification, not another fit to an aircraft recording.
The completed known-correction study, original constant-gravity controls and all
observed-pilot failures remain unchanged. Seven ESA confirmation groups stay closed.

## Fixed examples and information boundary

Use the independent Cartesian generator's northern 55° climbing/turning profile,
from 1,500 to 3,500 m over 1,200 seconds, with its existing `fast` body motion.
Retain 300 Hz engineering-unit samples and linear-point interval construction.
Use the existing nonzero sensor/antenna corrections: positive sign for the
zero-removal cases and negative sign for profiled-removal cases. The common
height-dependent gravity law is declared for every candidate.

Freeze 24 cases: three generating candidates × zero-removal or profiled-removal
fit × two working receiver-error cases × two fixed starts. Zero-removal truth is
zero; profiled-removal truth is 0.35. Use starts zero and the existing alternating
±0.001 pattern. Supply neither true initial state nor true calibration to fitting.

Queries are `0.5 + j` seconds for `j = 0..1199`. The earlier 800 receiver positions
determine initialization, covariance and calibration. The later 400 positions are
opened for scoring only after the continuous forecast is saved. No reset or
correction from later positions is allowed.

Bind the gravity anchor to the first **training receiver** height. It must not use
true initial height, later receiver heights or the scored residual. Evaluate the
gravity law at predicted midpoint height, retaining all existing nuisance columns
and bounds. Reuse the shared training/forecast path; do not create a study-specific
optimizer or weaken its stopping checks.

The original constant-mode weighted controls and exact archived-source comparisons
remain the compatibility reference. This new matrix tests the changed height mode;
it does not repeat completed constant-mode allowances. Its single northern climbing
geometry limits what this particular qualification establishes.

## Separate finite allowance and gate

Each case permits at most 200 training evaluations and one full-history forecast:
**4,824 native calls** across 24 cases, with no retries. Bound the training prefix
at 239,855 intervals for the stated queries and ±0.01 s latency support. The packet/
query allowance is `24 × (200 × 239855 × 800 + 360000 × 1200)`, or
**931,411,200,000 visits**. Reserve before execution and preserve interrupted charges.

Four workers use one numerical thread each, with a cooperative eight-hour ceiling.
Measured prior runs suggest hours rather than minutes at the evaluation ceiling;
this is an upper bound, not a request to consume every evaluation.

Keep both versioned working receiver-error policies and the existing parameter
bounds. Supply no random measurement noise in these first software controls;
passing cannot establish empirical covariance coverage or instrument precision.
Require numerical convergence, all 26 or 27 active columns, saved-forecast-before-
scoring provenance and the existing generated accuracy limits in both sections:
horizontal/height RMS ≤0.1 m and maximum spatial error ≤0.5 m, matching the original
weighted training controls. Preserve every failure.

Source/environment-bound checks must establish the earlier-only gravity anchor,
unchanged default generation, all input boundaries and finite accounting before
preparation. Verify all outputs and journals from saved evidence only. A failed
case blocks dependent observed refitting; it cannot be relabeled from a probe.

Deterministic generated rate arrays are represented by frozen source, environment,
recipe and full/prefix hashes, rather than repeated large array archives. Save
earlier receiver rows, forecasts, scoring geometry and before/after input-hash
bindings. Exact raw regeneration remains reproducible separately; the saved-only
audit verifies bindings and physical errors without regenerating raw arrays.
No original measurement is removed by this generated-data storage policy.

## What follows

Only a qualified pipeline may enter a separately frozen observed development
comparison with the original interval and unchanged physical-accuracy thresholds.
Neither this qualification nor that development comparison releases confirmation
data or establishes calibrated statistical significance.

[Gravity controls](../esa-gravity-controls/README.md) ·
[Prediction safeguards](../PREDICTION_VALIDATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
