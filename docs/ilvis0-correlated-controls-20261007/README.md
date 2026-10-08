# Joint IMU/GPS checks with correlated position errors

The existing joint IMU/GPS estimator now has a separate deterministic check of how
correlated position errors affect calibration and timing. Five analytic fixtures are
evaluated under all thirteen previously declared GPS-error assumptions. The fixtures
have known motion and sensor errors; they are not simulations of complete flights or
fits to the archived IMU data. The two structural offset/drift checks are separate.

All **65 cases completed with their expected outcomes**: 52 individually identifiable
cases recover the known value, while all thirteen orientation/bias cases retain an
unresolved direction. Both structural checks pass. The completed run used 65 control
starts, 1,309 fit residual evaluations, 247 additional precision predictions and three
structural predictions. No failed cases were replaced or selected away.

## Recovery and useful precision are different

An IMU measures angular increments and specific force. The estimator integrates those
measurements and compares its predicted antenna positions with GPS coordinates. These
controls vary acceleration bias, effective initial orientation, accelerometer gain and
GPS/IMU timing individually. A fifth fixture leaves orientation and two acceleration
bias components free together, where the observations cannot resolve all three.

Both recoverability and precision are reported. Recovering a known value from noiseless
positions does not establish that the value can be measured accurately with noisy data.
The local precision calculation propagates the complete assumed GPS covariance through
the nuisance Jacobian. It preserves correlations across times and axes. Marginal
uncertainties are not assigned when the Jacobian has an unresolved direction.

The tests use two-second translation fixtures with 200 native IMU intervals and seven
actual GPS epochs. The baseline one-millimetre position uncertainty and cross-axis terms
are **software fixtures, not receiver or instrument specifications**. The twelve added
cases use the previous 1/3, 3/10 and 10/30 metre horizontal/vertical scales, each with
independent noise or 10/60/300-second correlation, plus common offsets and endpoint drift.
Those scales are assumptions, not independently supported error bounds. The label
`formal_only` here refers to the toy baseline, not the archived position solutions.

Only the covariance changes between the thirteen cases; native IMU increments, GPS
coordinates, timestamps, parameter bounds and truth stay fixed. This tests correlated
weighting without interpolating measurements or smoothing away brief motion. All fits
use the existing frozen estimator, which is unchanged. The chosen analytic coordinate
metric is declared explicitly and is used only for these controls, never to infer Earth's
shape or assign a different observation covariance to each scientific candidate.

For illustration, the following local standard deviations compare the millimetre toy
baseline with the smallest 60-second correlated case, including its offset and drift.
Each parameter varies alone, with the other quantities fixed.

| Parameter | Toy baseline | Added assumed correlated errors |
|---|---:|---:|
| Acceleration bias | 0.00045 m/s² | 0.311 m/s² |
| Effective orientation | 0.000046 rad | 0.0317 rad |
| Accelerometer gain | 0.00080 fractional | 0.364 fractional |
| GPS/IMU timing offset | 0.00029 s | 0.407 s |

The noiseless fitter recovers these parameters in every one of the thirteen covariance
cases. Nevertheless, each illustrated correlated uncertainty exceeds that parameter's
declared control bound. These are unbounded local linearizations, not bounded intervals;
extrapolation outside the bounds indicates weak information, not a calibrated error bar.
Two-second recovery cannot establish useful archival calibration precision. Longer records,
appropriate motion excitation and independent instrument constraints require separate checks.

## Position and velocity have structural ambiguities

A one-metre GPS offset has the same observation response as a one-metre initial-position
shift in the translation fixture. A linear GPS drift has the same response as an
initial-velocity shift. Both checks compare the independently specified response with
the IMU/GPS predictor to within 1e-8 metres. Weighting correlated errors correctly does
not create information that separates these quantities. Independent constraints or
explicit nuisance treatment are necessary.

These are specific analytic controls. They do not prove universal ambiguity over every
aircraft maneuver, establish IMU mounting independently, or validate onboard corrections.
The effective orientation and mounting remain inseparable as independent parameters.

## Reproducibility and limits

Implementation: [control module](../../analysis/lll/ilvis0_correlated_controls.py),
[worker](../../analysis/tests/ilvis0_correlated_controls_worker.py), and
[focused tests](../../analysis/tests/test_ilvis0_correlated_controls.py).
Thirty-three distinct focused tests pass: eight new control/persistence tests, ten
preceding GPS sensitivity tests and fifteen estimator tests. They verify full-covariance
whitening, an independently calculated bias Jacobian/uncertainty, unchanged observations,
unresolved marginal precision, offset/drift ambiguities and interrupted/corrupted journals.

Each fit allows at most 160 residual evaluations, including the estimator's numerical
derivatives. Local precision uses at most seven additional predictor calls per case.
All counts are preserved. A separate append-only, fsynced control journal charges
interrupted starts before work; each of the 65 cases permits at most two starts. This
does not consume the empirical six-file/24-start Earth-fit allowance.

The run uses `data/ilvis0-correlated-controls-20261007/`, with its own frozen source/input/
environment manifest, source snapshots, atomic per-case results and hash checks. The
compact handoff includes the full compressed summary, start journal and
[parameter inventory](inventory.csv). [export_inventory.py](export_inventory.py) verifies
the evidence without repeating fits. Do not resume the completed worker or revise its
sources under this manifest. Every earlier completed study stays frozen.

These results do not establish archive calibration limits, physical integration/latency
semantics, or whether Group4 retains Earth rate. The short translation fixtures do not
characterize gyro performance or general aircraft rotations. All scientific decisions
remain abstentions. No archived observation, original file or scientific gate was changed;
all 232 originals remain and no empirical Earth-model fit ran.
