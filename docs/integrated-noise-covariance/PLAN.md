# Correlated errors from accumulated IMU noise

This software qualification adds a reusable state-space covariance operator.
It does not fit a flight, estimate archive noise, change a completed result or
open a protected recording. The existing receiver-error operator stays unchanged.

Accept explicitly supplied linear state transitions, independent process-noise
loadings, observation matrices, receiver-noise loadings and an initial-error
loading. The matrices and Gaussian error law are declared in advance; they
are not inferred from the residual being whitened. Loadings produce positive
semidefinite process covariance without clipping eigenvalues. Receiver
innovations must factor without jitter or repair.

Compute sequential innovations and their log determinant with storage linear
in the number of epochs. Apply exactly the same operator to residual vectors
and every Jacobian column. Support inversion and explicit continuous block
checkpoints; reject changed configurations, skipped epochs or changed column
counts. Check the declared storage cap before consuming the step iterator.

Provide a separate constant-level, small-angle example with continuous white
gyro and accelerometer errors. Its three-axis covariance must agree with the
analytic impulse-response integrals, including cross-time terms. This example
has a perfect initial state and does not describe the turning/climbing aircraft
or supply calibrated uncertainty for a flight.

Qualification compares small problems with independently assembled dense
covariance and Cholesky whitening, including nonuniform epochs, changing
transitions, cross-axis receiver covariance and all 27 columns. Test zero and
duplicated columns, inversion, block continuity, input preservation, rejection
of invalid/singular matrices and failure before allocation at a storage cap.

One scalability check uses 64,080 generated epochs and eight latent states,
with a 128 MiB stored-operator cap. No dense reference is constructed for this
long case. Short dense controls use at most 32 epochs. All tests use one
numerical thread, reserve the three active workers and perform no native
trajectory calls, optimizer starts, original reads or protected reads. No
stochastic draws or fitted outcomes are used to select these tests.

Source-bound local qualification must pass before publishing the component as
software checked. A time-varying flight error model, estimated-parameter
uncertainty, empirical noise assessment and coverage calibration remain separate
gates. Existing physical accuracy targets and the running noise study are fixed.

[Analytic error budget](../esa-noisy-prediction/ERROR_BUDGET.md) ·
[Prediction assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
