# Matching measurement bandwidth

Aircraft motion is much larger than the rotation the experiment seeks. The motion
correction and the IMU measurement therefore need compatible filtering: otherwise
one can subtract a smoothed estimate of a maneuver from a sharper recording of it.

This study checks that issue using the six existing simulated recordings and their
completed joint fits. It creates no new flights and performs no optimization.
The fitted wind, orientation and drift parameters stay fixed. These are simulated
IMU recordings following an observed airline route, not measurements from a real IMU.

The check averages calibrated gyro samples into one-second intervals, maps them
into a common orientation, and applies a 30-second Hann filter. The complete
reconstructed prediction receives the same additional filter before both are
averaged into minutes. GPS and accelerometer inputs already received a 30-second
filter in the joint fit. Filtering stops at gaps and IMU turns. The extra output
filter leaves 79 of the original 83 minutes; all comparisons below use those same
79 minutes.

| Simulated truth | Wind description | Before extra filtering | After identical filtering |
| --- | --- | ---: | ---: |
| Rotating globe | Broad wind spline | 8.26°/hour | 7.40°/hour |
| Rotating globe | Physical wind and airspeed | 7.85°/hour | 7.08°/hour |
| Stationary globe | Broad wind spline | 8.27°/hour | 7.44°/hour |
| Stationary globe | Physical wind and airspeed | 7.96°/hour | 7.21°/hour |
| Disc | Broad wind spline | 8.32°/hour | 7.48°/hour |
| Disc | Physical wind and airspeed | 7.93°/hour | 7.16°/hour |

The improvement is about 9–10%. Bandwidth matters, but it does not account for most
of the remaining variation. Reconstructing the original joint motion closes exactly
at the saved numerical precision. The slower science and drift predictions are
interpolated within each uninterrupted mounting interval; that approximation changes
minute predictions by only 0.026–0.040°/hour in these cases. Reaveraging the gyro
changes it by about 0.34°/hour. Neither change explains the residual scale.

Filtering also makes neighboring measurements share samples. The study carries
that overlap through an explicit covariance matrix, including correlations between
axes and the changes in IMU orientation. Under the provisional assumption of
independent one-second gyro errors, its typical marginal scale is about
3.53°/hour. This estimate uses observed variation within each second, which includes
aircraft motion; it is not a measurement of the device's white noise.

The fitted residuals show neighboring-minute correlations reaching about −0.61 on
one reference axis. Their correlations are descriptive: the fit itself can introduce
correlations, and these six cases share simulation seeds. They cannot identify an
error source or establish statistical significance. They do show why the remaining
uncertainty work must address time dependence and shared GPS/accelerometer errors,
rather than treating the residual scale as independent IMU noise.

The next step is a continuous measurement equation with consistent filters for
every term, followed by propagation of GPS, accelerometer and gyro errors together,
including the effect of fitting nuisance parameters. The present interpolation and
gyro-only covariance are diagnostics, not a new likelihood or calibrated decision
rule. Production analysis and eligibility remain unchanged.

The documented corpus contains `review.json`, six task-named compressed array
archives, and `verification.json`. The report binds saved inputs, fitted checkpoints,
helper sources and the numerical environment. The independent verifier checks
archive hashes, residual arithmetic, common support, prediction closure and positive
semidefinite covariance. Five new tests cover exact filter transfer, gaps/turns,
rotation of covariance, shared samples and joint-motion reconstruction; 21 focused
checks pass across this work and the earlier acceleration studies. No worker remains
active. Completed results are immutable; further fitting needs its own finite scope.
