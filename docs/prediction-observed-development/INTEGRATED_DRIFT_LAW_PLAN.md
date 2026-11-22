# Candidate for changing forecast error

The current ESA forecasts can be close over 120 seconds, but their stated
uncertainty has not been shown to cover aircraft prediction errors. A
samplewise worst-case calculation is too broad. This plan tests a compact
time-correlated **candidate**, without treating it as the aircraft's law.

Model the remaining position error with three linked quantities on each
north/east/up axis: position, velocity and acceleration error. Allow both
white acceleration error and a slowly changing acceleration error driven by
white jerk. Keep both persistent receiver-position drift and independent
per-report receiver error. Initial position, velocity, acceleration and
receiver-offset uncertainty are separate inputs, with no values inferred
silently from the ESA recording.

The candidate uses the existing linear-memory innovations operator. First
compare its covariance with an independently integrated dense reference;
check future uncertainty growth, conditioning on earlier errors and invalid
inputs. Then test full-pipeline forecasts on independently generated aircraft
histories, including changed motion and changing-bias adversaries. Fit any
law parameters on earlier data only and score later reports only after the
forecast is sealed. Preserve numerical failures.

The first four covariance/conditioning checks pass. A separate
[generated-IMU integrator](../../analysis/lll/esa_generated_imu_propagation.py)
passes three stream and corruption checks. On a clean 120-second, 300 Hz
control its position differs from the analytic path by at most 0.000036 m;
this checks the local propagation code, not an aircraft error law. A
1,200-epoch candidate operator uses 2.16 MB and produces a 400-epoch
conditional forecast without reading future residuals.

Passing the covariance checks qualifies only the propagation calculation.
The aircraft law, parameter bounds, calibration uncertainty, absolute
adequacy and new-flight coverage remain open. The seven reserved ESA groups
stay closed until those gates and their confirmation identities are frozen.

The [first frozen generated pilot](integrated-drift-pilot/RESULT.md) then
closed 8/8 technical tasks. Only 3/8 generated histories kept every withheld
coordinate inside the law's nominal marginal ranges. A conservative
simultaneous bound retained 6/8. These eight draws do not estimate a coverage
rate or formally reject the law; they leave it unqualified for the tested
mixture. Its omission
of the generator's changing gyro-bias walk is one plausible contributor;
the pilot cannot isolate the cause. A revised candidate needs a separate
seed cohort and its own frozen acceptance rule.
