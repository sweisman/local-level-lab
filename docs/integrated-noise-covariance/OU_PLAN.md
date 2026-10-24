# Include slowly changing bias in the generated error example

Extend the checked constant-level example to independent stationary
Ornstein–Uhlenbeck gyro and accelerometer biases, alongside white rate noise.
Use thirteen states: angle, velocity, position and two changing biases on
each horizontal axis; velocity, position and acceleration bias vertically.
Initialize only the bias states at their declared stationary variance.

Integrate the continuous linear state transition and diffusion covariance over
each actual interval with a matrix exponential. Factor the resulting process
covariance without eigenvalue clipping, jitter or variance floors. This
prototype requires strictly positive driver amplitudes; zero variances are not
silently replaced. The existing white-only example remains available.

Compare the position covariance with independent double integration of the
stationary bias kernel, including cross-time terms. Also compare conditional
OU endpoint/integral moments with the separately implemented noise generator,
including a 1/300-second interval. Test earlier-only conditional predictions
against dense conditioning. Reject invalid inputs and check the storage cap
before calculating matrix exponentials.

Check the running experiment's explicit stress amplitudes at intervals of
1/300, 1 and 400 seconds, without treating those amplitudes as device limits.

New dense examples use at most eight generated epochs. Retain all earlier
whitening, conditioning and 64,080-epoch storage controls. Use one numerical
thread, reserve the two remaining active workers and perform no random draws,
native trajectory calls, optimizer starts, original reads or protected reads.
Preserve both earlier qualification snapshots and bind this extension's own
source/environment/test report before publication.

This matches the process family declared by the running noise experiment in
a constant-level approximation. It does not model the aircraft's time-varying
kinematics, receiver persistence or fitted-calibration uncertainty, estimate
instrument noise, change a running study or authorize observed fitting.

[Component overview](README.md) · [Prediction assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md).
