# Generated fits do not recover their known calibration closely

The [saved audit](GENERATED_CALIBRATION_RECOVERY_PLAN.md) compares each
closed fit with the calibration values used to generate its IMU record.
Differences are divided by each parameter's allowed half-range, so a value
of 1 means a difference equal to that half-range. All fourteen checked true
values were inside their declared bounds.

| Generated error law | RMS calibration difference | Fitted calibration parameters at a bound | Largest differences |
|---|---:|---|---|
| Increment | 0.469 half-ranges | Gravity adjustment; vertical accelerometer bias | Gravity 0.90, vertical accelerometer bias 0.85, Y gyro gain 0.71 |
| Point | 0.353 half-ranges | X gyro gain | X gyro gain 0.80, time offset 0.68, Z gyro gain 0.50 |

The two fits passed their numerical checks but missed their known later
physical paths by 108.6 m and 91.3 m horizontally. Their training data do
not force the fitted sensor calibration close to its known generating values.
That is a concrete reason to keep calibration uncertainty in the forecast.
This two-case audit cannot isolate which calibration difference caused the
path miss or establish an aircraft calibration rule. No fit was repeated and
no recorded aircraft data were read. The scientific decision remains
**abstain**.

[Verified machine report](generated-calibration-recovery-result.json) ·
[Original generated pilot](BOUND_AWARE_GENERATED_PILOT_V2_RESULT.md)
