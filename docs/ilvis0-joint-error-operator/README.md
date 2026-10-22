# Receiver and IMU errors over a complete record

The new calculation combines time-correlated receiver error with accumulated
IMU (inertial measurement unit) noise. It keeps their correlation across the
training/prediction boundary and never resets the noise-integration origin
when selecting a later interval.

**15 focused software checks pass; 59 pass with the existing inertial-noise and
shared-scale checks.** The comparisons include irregular times through
438 seconds, all 27 input columns, and agreement with a separately constructed
dense covariance reference. Turning off the IMU-noise contribution reproduces
the existing receiver-only calculation.

The implementation stores a small evolving error state instead of a square
matrix covering every observation. A 1,000-epoch test uses less than 1 MB of
operator storage. A larger archive-scale runtime trial has not yet run.

## What is assumed

The caller supplies the receiver covariance, accelerometer and gyroscope noise
spectra, and a constant matrix connecting small orientation error to acceleration
error. There are no hardware-performance defaults. The existing linear
[inertial-error equations](../ilvis0-inertial-error-controls/MATHEMATICS.md) are
unchanged. Receiver and inertial driving errors are assumed independent; their
accumulated observations remain correlated in time.

The operator predicts the error mean and coordinate variances from training
values only. It does not estimate calibration uncertainty, select a noise law,
read future positions or decide which physical model wins. Calibration must
remain in the separate shared-parameter prediction method.

## What this adds—and what remains

This connects the receiver and inertial error components in a calculation
suited to long histories. It does not show that the supplied Gaussian/linear
law describes the aircraft recordings. Variable flight dynamics, possible
processing effects, error-scale assessment and supported numerical allowances
still need explicit treatment before aircraft prediction coverage can be claimed.

[Source](../../analysis/lll/ilvis0_joint_error_operator.py) ·
[Tests](../../analysis/tests/test_ilvis0_joint_error_operator.py) ·
[Prediction-error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md)
