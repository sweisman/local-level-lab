# Include accumulated IMU error in prediction uncertainty

Receiver position error alone cannot describe an inertial prediction. Noise in
an **IMU (inertial measurement unit)** accumulates as velocity, orientation and
position error. This software component adds that contribution under explicit
linearized assumptions, without fitting aircraft observations.

## Scope

Use a nine-coordinate error state: position, velocity and small orientation
error, each with three axes. Acceleration noise enters velocity; gyro noise
enters orientation. A supplied constant three-by-three coupling maps orientation
error into acceleration error. Supply full cross-axis noise spectral matrices;
do not insert manufacturer performance numbers as raw-noise measurements.

Integrate this linear stochastic system analytically. Preserve the specified
origin even when the first position observation is later, and preserve
correlation across training and future times. Add the existing declared receiver
covariance before any conditioning. Return the complete small-problem covariance
in epoch-major three-coordinate order; cap the diagnostic at 512 epochs.
Existing frozen error-model and streaming implementations remain unchanged.

## Qualification

Focused deterministic tests compare the analytic transition and process
covariance with a separate matrix-exponential and numerical-quadrature reference.
Test irregular sampling, cross-axis signs, zero coupling, zero noise, three
candidate coupling examples, a four-minute horizon, interval subdivision,
time-origin preservation, positive definiteness with receiver error, coordinate
transforms and invalid inputs. These small tests use one numerical thread,
reserving one for the active growth screen. No optimizer or aircraft read runs.

## Limits

This is a supplied Gaussian, linearized, white-driving-noise model, not an
empirically established law for a recording. It does not establish that actual
IMU quantization errors are independent, cover unknown onboard corrections,
bound nonlinear stochastic propagation, or qualify an uncertain integration
clock. Initial state uncertainty and constant calibration belong to the separate
shared-calibration treatment; the component starts from zero stochastic error at
the declared origin. Dependence between receiver and inertial noise is assumed
absent, not demonstrated. Recording-length usefulness and whole-program numerical
bounds remain separate requirements of V01.

Success here qualifies the component mathematics only. It does not open V02,
change the 53-stretch findings or permit protected ESA outcome inspection.

[Error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
