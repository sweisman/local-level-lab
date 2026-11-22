# Where the ESA height ranges fail

Two saved forecasts on the same opened ESA development flight used different
calibration settings but the same conditional error law. Each predicted 400
later GPS receiver reports. Both height ranges began missing early and then
missed continuously:

| Calibration setting | First later report outside nominal 95% height range | Consecutive later misses | Final forecast minus receiver height |
|---|---:|---:|---:|
| Receiver-only fit | 24th | 377 | +27.97 m |
| IMU-error-weighted fit | 26th | 375 | +25.46 m |

The two signed height-error histories have **0.9999 correlation**, the same
sign at every report, and **0.99 m RMS difference**. The 95th percentile of
absolute error divided by declared standard deviation is 7.86 and 7.22,
respectively, versus 1.96 for a nominal two-sided 95% range. Descriptively,
this is about 4.01× and 3.68× the range's stated standard-deviation scale.
Those are **observed discrepancies**, not calibrated replacement factors.

Changing between these two fitted parameter settings does not remove the
height drift. A shared instrument, motion, clock or error-law deficiency could
produce it; this comparison does not identify the cause. The 400 reports are
one highly correlated sequence, not 400 independent validation flights.
An [earlier local-uncertainty study](LINEAR_UNCERTAINTY_V3_RESULT.md) added
uncertainty from all 26 fitted calibration parameters at one setting and
improved height coverage only from 25/400 to 26/400. The missing local linear
parameter variance alone therefore does not explain the miss under that law.
Over the 400-second forecast, a 25 m displacement is the scale produced by
either a constant 0.063 m/s starting vertical-velocity error or a constant
0.00032 m/s² acceleration error, considered separately. These are arithmetic
equivalents, not estimates of actual instrument error.

The next generated control should vary changing vertical motion, nonlinear
calibration effects and sensor error separately, then test whether a
prospectively fixed range covers new histories without erasing the useful
model contrasts. No fit was repeated, no original aircraft data were
reopened, and seven reserved ESA flight groups remain closed. The scientific
decision remains **abstain**.

[Machine report](cross-point-height-anatomy.json) ·
[Prior coverage check](CROSS_POINT_COVERAGE_RESULT.md) ·
[Fixed diagnostic plan](CROSS_POINT_HEIGHT_ANATOMY_PLAN.md).
