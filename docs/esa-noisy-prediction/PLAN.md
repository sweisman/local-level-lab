# Prediction tests with known measurement errors

## Purpose

The completed long software controls used noiseless measurements. The next
test adds known receiver errors, gyroscope noise, accelerometer noise and
slowly changing sensor bias. It asks how the existing training-only estimator
behaves when these errors occur together.

This is a generated-data robustness study, not an estimate of the archive's
actual noise or a calibration of scientific confidence. The existing receiver
weights remain fixed: they must not be enlarged because a candidate fits badly.
A receiver-only weight does not become a complete IMU prediction-error model.

## Input qualification

Use the shared `lll.measurement_noise` generator and
`lll.airquantumgrav_noisy_inputs` constructor. Apply errors before initialization
and fitting, including the first receiver height used to anchor gravity.
The fitter receives noisy increments and earlier noisy positions only, without
true calibration, attitude or initial state.

White sensor errors integrate with the square root of the actual sample
interval. Slowly changing bias uses a stationary Ornstein–Uhlenbeck process;
its interval integral and endpoint are generated jointly. Do not approximate
an entire interval by its endpoint bias. Retain their correlation and support
uninterrupted continuation.

Receiver errors preserve the supplied cross-axis covariance, temporal
correlation and fixed drift origin. Use independent named random streams for
receiver, gyro, accelerometer, white noise and changing bias. Extending later
samples must leave the earlier generated noise unchanged. Reject invalid
covariance or timing without clipping or repair.

The input checks include high-precision integral identities, independently
written covariance expectations, irregular timing, zero noise, exact prefix
reproducibility and all six model/processing combinations. These checks qualify
input generation; they do not qualify noisy fitting or aircraft uncertainty.

## Declared stress settings

These are development assumptions, not measured instrument specifications.
They are fixed before the noisy fitting results are examined.

| Component | Setting |
|---|---|
| Gyro white angle noise | 0.02°/√hour |
| Accelerometer white increment noise | 0.0002 m/s/√second |
| Gyro changing bias | Stationary standard deviation 0.05°/hour; 600-second correlation time |
| Accelerometer changing bias | Stationary standard deviation 0.00005 m/s²; 300-second correlation time |
| Receiver errors | Each of the two existing versioned working error policies, with full cross-axis covariance |
| Reproducibility | Seed 26062413; named PCG64 streams; frozen numerical environment |

Keep the existing constant calibration bounds as well. Changing bias and
constant offset are distinct. Match the same sensor-noise realization across
starts and receiver-weight cases; preserve both receiver policies.

## Fitting and scoring

Reuse the qualified wider-precision training/forecast path. The matrix has
three generating physical candidates, two processing cases, two receiver
policies and two starts: **24 identities**. Each candidate is tested against
data generated under that candidate; this is not an observed model-selection
campaign. Keep the twenty-minute turning/climbing trajectory, 800 training
positions and 400 later query epochs, with all 26/27 nuisance columns.

Generate later truth positions only after the continuous forecast is saved.
Score against known physical truth, without adding later receiver noise to hide
reconstruction error. Use the existing observed-prediction accuracy screen:
horizontal RMS 10 m, height RMS 30 m, maximum horizontal error 50 m and maximum
absolute height error 150 m. Report numerical completion and physical accuracy
separately. The earlier noiseless software targets and results remain unchanged.

Before execution, qualify the actual fitting adapter and reporter, including
absence of later-position influence, noisy initialization, complete derivative
columns, native accounting and preservation of failures. Input-generator tests
alone do not release this study.

## Separate finite allowance

Freeze the final definition before execution. Allow 24 starts, at most 200
fitting evaluations and one forecast each, four single-thread workers and a
cooperative eight-hour ceiling. This is a new allowance, not unused work from
a completed study. Native-call ceiling: 4,824. Packet/query work ceiling:
931,411,200,000. No retries or transfers between starts.

Per identity, charge at most 360,000 constructed intervals, 360,801 generated
samples before scoring, 1,200 later truth samples and 6,484,812 normal variates.
Charge before work and preserve failed or interrupted starts. Archive original
integer measurements, observed fits and protected data are not inputs.

Results can expose a failure of the working error assumptions or estimator.
Do not change bounds, noise amplitudes, stopping checks or accuracy limits
after seeing an outcome to make the study pass. A failed gate blocks dependent
confirmation work; separate diagnosis remains permitted.

The 53-stretch baseline and seven protected ESA confirmation groups stay
unchanged. These tests do not identify a rotation field's cause or establish a
solar-versus-sidereal distinction.

[Error diagnostic](../esa-error-structure/INTERPRETATION.md) ·
[Prediction protocol](../PREDICTION_VALIDATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
