# Duration, motion excitation and joint IMU/GPS calibration

The bounded duration/motion checks are complete: **18 analytic trajectory/tangent controls
and four gyro-bias/timing recovery controls**, with no trajectory or recovery failures.
Eleven focused tests pass. The longest trajectory agrees with the independently calculated
positions to within 1.5e-9 metres. These are software controls, not archived-flight fits,
measured sensor performance or Earth-model results.

## What changed from the two-second checks

The controls compare 2-, 20- and 60-second records, with varying forward acceleration at
an initial 200m/s. Each duration has both a steady orientation and a one-second triangular
pitch excursion reaching 0.1 degrees and returning to the starting attitude. This preserves
brief motion of the scale reported from the flight camera; the footage supplies context,
not the control's measured ground truth.

GPS positions are calculated by independently integrating the specified piecewise-constant
acceleration. Rotations use an independently written one-axis sine/cosine matrix. The
existing unchanged IMU/GPS predictor is tested against those positions. The pitch event is
resolved at 200Hz. Outside it, half-second intervals exactly represent constant orientation
and acceleration. This is a property of the analytic fixture; no archive data is averaged,
downsampled or interpolated.

The tangents allow eight nuisance parameters together: initial position, velocity and
effective pitch, gyro bias/gain, acceleration bias/gain, and GPS/IMU timing. They compare
the toy one-millimetre baseline with two previously declared correlated-error assumptions:
1/3m horizontal/vertical at60seconds, and10/30m at300seconds, each including offset/drift.
Observations, truths and bounds stay fixed as covariance changes. These assumed scales
are not measured uncertainty bounds for the archive.

Four separate single-parameter fits recover an injected gyro bias of2e-6rad/s or timing
offset of0.035seconds at20/60seconds. Other quantities are fixed in those fits. Their
success does not establish simultaneous calibration of all eight parameters.

## What the controls show

The table uses the smaller correlated case with the pitch excursion. Values are local,
unbounded standard deviations with all eight nuisance parameters free.

| Quantity | 20 seconds | 60 seconds |
|---|---:|---:|
| Gyro bias | 3.10e-4 rad/s | 1.81e-5 rad/s |
| Acceleration bias | 0.688 m/s² | 0.105 m/s² |
| GPS/IMU timing | 0.210 s | 0.116 s |
| Gyro gain, fractional | 21.2 | 11.4 |

Duration improves the information in this fixture. It does not make the assumed errors
small or the nuisance parameters precisely known. In particular, these local gyro-gain
uncertainties greatly exceed the declared fractional bound of0.01. They are sensitivity
indicators extrapolating beyond the bounds, not plausible physical gain estimates or
calibrated confidence intervals. Large unresolved uncertainties must not be replaced by
the small errors from single-parameter noiseless fits.

Without rotation, the gyro-gain direction is exactly unobservable. A one-parameter test
detects information when the pitch excursion is added, but the joint eight-parameter
problem remains much weaker. The rank diagnostic reports5of8directions for both two-second
fixtures; longer steady-orientation fixtures report7of8. Longer pitch fixtures report7
with the toy baseline and8with the correlated cases. **That covariance-dependent rank
change is preserved, not interpreted as better data when errors increase.** The cutoff
depends on weighted singular values and disagreement between two derivative steps.
Rank alone is insufficient: the reported uncertainty relative to the declared bounds
also matters. This provisional local diagnostic is not a scientific eligibility rule.

Partial precision is handled explicitly. A parameter with a component in the unresolved
subspace gets no finite marginal uncertainty. The code never reports the diagonal of a
pseudoinverse as precision for a null direction. Identifiable parameters can retain local
precision when a different parameter is unresolved, as tested on an independent matrix.

## What remains for the actual instruments

The [instrument evidence review](INSTRUMENT_EVIDENCE.md) distinguishes empirical unit and
axis checks from unsupported calibration, integration-clock, latency and processing
assumptions. Public documentation confirms the packet structure but does not establish
legacy IMU6 Earth-rate retention or hardware-specific noise/drift bounds. IMU8 performance
is not transferred to IMU6. No manufacturer inquiry was sent.

The useful next step is instrument-specific evidence for those assumptions and a stable
information/precision criterion under derivative and covariance changes. Further noiseless
recovery checks cannot supply the missing physical evidence. Any observed Earth comparison
still requires its independent-evidence gate, uses the separate finite allowance, and must
retain abstentions, failures and conditional assumptions.

## Reproducibility

Implementation: [control module](../../analysis/lll/ilvis0_excitation_controls.py),
[worker](../../analysis/tests/ilvis0_excitation_worker.py), and
[tests](../../analysis/tests/test_ilvis0_excitation_controls.py). Eight new tests cover
independent integrals, native pitch resolution, analytic trajectory agreement, covariance
and measurement identity, partial/null precision, excitation, bounded timing recovery and
input guards. Three preceding tests verify the unchanged empirical evidence gate, full
covariance weighting and derivative-evaluation budget.

The completed run used22control starts,324tangent/trajectory prediction evaluations and
59recovery residual evaluations. Its separate journal counts interrupted starts, with
at most two starts per task. Source/input/environment manifests, snapshots, per-task
atomic hash-checked reports and completion are frozen in `data/ilvis0-excitation-20261007/`.
This directory preserves compact results and the [parameter inventory](inventory.csv).
[export_inventory.py](export_inventory.py) verifies and rebuilds the compact handoff.
Do not resume the completed worker or mix revised code into its manifest; older studies
remain frozen. All232originals remain. Earth fits/starts, scientific gate changes,
downloads, deletions and synthetic flight campaigns remain zero.
