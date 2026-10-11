# A numerical source of apparent gyro offset

**Accounting for rotation within each 200 Hz measurement greatly improves recovery
of a known gyro offset.** All nine new software fits completed and passed their
predefined convergence and track-prediction checks. No NASA recordings were refitted.

An **IMU (inertial measurement unit)** measures turning and acceleration. The
controls supply independently integrated measurements from a known moving instrument.
The instrument turns throughout each five-millisecond measurement, rather than only
between measurements. Treating each measurement as one simple rotation and one
acceleration in a fixed direction introduces a small integration error.

The earlier tests showed that this small error could produce a much larger fitted
gyro offset when the track provided little information to distinguish calibration
parameters. They also showed that reducing the measurement interval reduced that
error. This comparison instead keeps the original 200 Hz measurements and accounts
for the motion within them. It inserts no extra samples.

## What the comparison found

Each control contains a known +0.25°/hour Z-axis gyro offset. The table shows the
**error in the recovered offset**, rather than the offset itself:

| Supplied physical truth | Original integration | Changing-axis correction only | Rotating-force correction only | Both corrections |
|---|---:|---:|---:|---:|
| Rotating globe | +0.6463°/hour | +0.6129°/hour | +0.03041°/hour | −0.00001038°/hour |
| Stationary globe | +0.5381°/hour | +0.4968°/hour | +0.03472°/hour | −0.00000548°/hour |
| Stationary disc | +0.4512°/hour | +0.4166°/hour | +0.03568°/hour | +0.00037653°/hour |

The changing-axis correction is called **coning**. The rotating-force correction
includes **sculling**. Using both reduces offset error by about 62,000 times,
98,000 times and 1,200 times respectively. No fitted parameter reached its limit
in these nine new fits.

The independent check at the injected calibration tells the same story: maximum
position error falls from about 41 micrometres to 0.26 nanometres. These are
noise-free software controls, so that extraordinarily small final error measures
agreement between calculations; it is not a claim about real positioning accuracy.

Both corrections matter. The original and corrected calculations still have almost
the same weak calibration direction: their local condition numbers remain around
12 million. Better integration removes the error that this weak direction amplified;
it does not make the geometry informative enough to recover calibration reliably
from noisy measurements.

## What this establishes

The short controls now reproduce the injected calibration much more accurately at
the original rate, using the original solver and calibration limits. Independent
continuous integration checks the correction formulas; focused tests also check
derivatives, partial measurements, unequal packet spacing and exact agreement with
the old predictor when corrections are disabled.

This is a meaningful explanation of the earlier **software-control** offset errors.
It is not yet an explanation of the calibration limits reached in the NASA fits.
The controls cover 12-second equatorial tracks, six free parameters and one starting
point for each new fit. Each physical model is tested against its own independently
generated observations. This comparison does not select an Earth model.

The correction assumes ordinary integrated angular rates and specific force. It
must not be applied a second time to measurements that already incorporate the same
compensation. The NASA stream's relevant processing convention remains to be tested.
The existing NASA results and scientific decision gate are unchanged.

See the [complete report](README.md), [frozen plan](PLAN.md) and
[next qualification step](NEXT_STEP.md). The run used nine starts and 359 new native
integration sweeps, including 15 predictions at known calibration. It used two
numerical threads and no retries. All 34 focused tests passed.
