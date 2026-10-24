# Learning calibration before predicting later positions

## Purpose and dependency

The [antenna and calibration controls](../esa-observation-controls/README.md)
supply the correct calibration vector. This next E01 test must estimate it
using earlier observations instead. It may start only after that calculation
qualifies and the new source-bound software tests pass.

This remains a generated-data qualification. No ESA recording, including
recording 187, is fitted. Reserved confirmation groups remain untouched.

## Fixed experiment

Use the independent Cartesian trajectories and synthetic sensor transformations
from `lll.airquantumgrav_truth` and `lll.airquantumgrav_observation_truth`.
Keep the earlier fast-maneuver pattern, but use 120 seconds at 300 Hz for this
estimation check. The preceding controls test twenty-minute forward propagation;
this shorter study tests training-only estimation and prediction together.

There are 24 identities: three generating candidates, two latitude signs
(−55° and +55°), two processing cases and two predetermined starts. Each fit
uses its generating candidate. This qualifies fitting behavior; a full
three-candidate decision calibration is a later, separate study.

- The zero-removal case generates removal 0 and fixes it at 0 in the fit.
  The profiled case generates removal 0.35 and estimates a common fraction in
  `[0,1]`. The same conventional vector defines removal for every geometry.
- Use positive synthetic bias/gain/antenna errors in the zero-removal case and
  their negative counterparts in the profiled case. Preserve the exact raw
  generated samples and constructed increments.
- Receiver query times are 0.5 through 118.5 seconds, one second apart. Fit the
  first 79 epochs only, ending at 78.5 seconds. Score the remaining 40 afterward.
- Receiver truth is the independent Cartesian antenna point at the declared
  latency, converted to the generating coordinates. The generator must not
  import the predictor or use it to produce this truth.
- Initialization uses only the earlier receiver positions and raw IMU prefix,
  through the existing training-only initializer. Do not supply the true attitude,
  velocity, gravity or correction vector to initialization or fitting.
- Fixed software-fixture domains: initial attitude X/Y ±0.25 rad and Z ±π rad;
  velocity ±20 m/s; initial position ±100 m; gyro bias ±1°/h; accelerometer bias
  ±0.1 m/s²; gyro gain ±0.01; accelerometer gain ±0.02; antenna offset ±5 m;
  gravity correction ±0.1 m/s²; latency ±0.01 s. These are synthetic-test bounds,
  not measured ESA device limits. Retain all 26 or 27 active columns.
- The training covariance is fixed at independent 0.01 m standard deviation
  per axis in the declared generating local metric. It is a noiseless software
  fixture weight, not an estimated receiver-error law. Its coordinate conversion
  uses training positions only. No later position determines weights or starts.
- Starts are normalized zero and alternating −0.001/+0.001 by active-column
  order. Use the qualified near-zero stopping composition with the ordinary
  nonzero-cost gate preserved. Choose no new starts after seeing results.
- Every fit must meet its numerical stopping rule and preserve every nuisance
  column. Training and later horizontal and height RMS must each be at most
  0.1 m; maximum spatial error at most 0.5 m. These descriptive software targets
  do not establish coverage or uniqueness of the recovered calibration.

## Allowance and evidence

Each identity allows 200 native fitting calls, including fresh stopping checks,
plus one continuous forecast. Reserve at most 201 calls × 36,000 packets × 119
queries per identity: 4,824 calls and 20,666,016,000 conservative packet/query
visits in total. One worker uses four numerical threads, with a cooperative
two-hour ceiling and no retries. Later positions are opened for scoring only
after the forecast artifact is saved. Interrupted starts remain charged.

Charge construction before work and record array/source/environment hashes.
Each case generates 36,001 rate samples and 79 earlier receiver samples, then
regenerates all 119 receiver samples for scoring after the forecast is saved.
The repeated earlier positions must match exactly. Its separate construction
allowance is 36,000 intervals and 36,199 generated samples per identity:
864,000 intervals and 868,776 generated samples across the complete matrix.
Raw rate/increment arrays use a compressed, hash-bound NumPy archive; training
positions and post-forecast scoring positions remain separate JSON artifacts.
Freeze a separate definition and allowance; completed work cannot fund this test.
Preserve every fit, failure, active column, forecast and error curve. Publishing
reads saved artifacts only. No change to the original NASA findings is implied.

## Shared implementation and verification

1. Extend the independent observation geometry with Cartesian-to-coordinate
   conversion. Check it against separate geometric identities and both latitude
   signs; keep navigation imports absent.
2. Add a small `lll.airquantumgrav_training_controls` definition/evaluator that
   calls the existing training initialization, fit and forecast components.
   Keep generated raw inputs and later receiver positions in separate artifacts.
3. Test earlier/later isolation, all columns, native/construction charges, complete
   timing support and source-bound preparation before launch. Use real short
   native examples; do not initialize from supplied true calibration.
4. Audit closed results and publish every outcome. A failure blocks observed
   ESA fits, while receiver-error diagnosis and other independent roadmap work
   may continue. Do not widen targets or an active allowance to obtain a pass.

## What remains afterward

Even a complete pass does not identify actual rate averaging or filtering,
calibrate receiver covariance, establish installation continuity or validate
twenty-minute calibration recovery. Those requirements need explicit assessment
before a receiver-only selection revision and observed ESA comparison.

[Roadmap](../ANALYSIS_ROADMAP.md) · [Prediction safeguards](../PREDICTION_VALIDATION.md).
