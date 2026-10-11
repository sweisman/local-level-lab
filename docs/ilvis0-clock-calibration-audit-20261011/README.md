# What changed when the clock was refitted?

**All six clock fits converged and preserved globe over flat, followed by rotating over still globe, under both processing cases.** This report compares saved parameters from the same 7.30-minute stretch, with median ground speed 878.1 km/h. Its IMU record type is 21. An IMU (inertial measurement unit) measures turning and acceleration. These are repeats of one stretch, not independent flights.

## The clock discrepancy is absorbed by calibration readjustment

Changing the clock at the old parameters raised rotating-globe vertical error from about 0.70 m to 9.36 m. Refitting restored it to about 0.70 m. The objective changed by only about 0.12%. Both clocks therefore produce similar optimized track errors here, despite different calibration estimates.

| Processing case | Model | Nominal cost | Header cost | Cost change (%) | Parameters at limits, nominal / header |
|---|---|---:|---:|---:|---:|
| bias1_unsubtracted | sphere_rotating | 2.31103 | 2.30817 | -0.12377 | 3 / 2 |
| bias1_unsubtracted | sphere_still | 10747 | 10748.6 | 0.01438 | 14 / 14 |
| bias1_unsubtracted | flat_still | 49304.2 | 49303 | -0.00247 | 15 / 15 |
| bias1_profiled_removal | sphere_rotating | 2.31103 | 2.30814 | -0.12488 | 4 / 3 |
| bias1_profiled_removal | sphere_still | 10747 | 10748.6 | 0.01438 | 15 / 15 |
| bias1_profiled_removal | flat_still | 45776.4 | 45775.7 | -0.00151 | 15 / 15 |

Cost is the saved sum of squared covariance-scaled receiver errors. It is not a detection significance or a hardware calibration measurement.

## Which parameters moved?

The table below shows the preferred rotating-globe fits. Gravity correction leaves its lower limit under header timing; accelerometer offset, X/Y gyro gains and timing offset also move. This shows that these estimates can readjust together. A two-clock comparison cannot attribute the change to one parameter or identify the physical cause. No new Jacobian or covariance was calculated.

| Processing case | Parameter | Unit | Nominal value | Header value | Change | Limits, nominal / header |
|---|---|---|---:|---:|---:|---|
| bias1_unsubtracted | gyro_bias_z | deg/hour | 1 | 1 | 0 | upper / upper |
| bias1_unsubtracted | accel_bias_z | m/s2 | -0.00663631 | 0.0310887 | 0.037725 | interior / interior |
| bias1_unsubtracted | gyro_gain_x | % | -0.02325 | 0.410898 | 0.434148 | interior / interior |
| bias1_unsubtracted | gyro_gain_y | % | -0.143765 | 0.264927 | 0.408692 | interior / interior |
| bias1_unsubtracted | gyro_gain_z | % | -2 | -2 | 0 | lower / lower |
| bias1_unsubtracted | gravity_delta | m/s2 | -0.05 | -0.00839876 | 0.0416012 | lower / interior |
| bias1_unsubtracted | time_offset | s | 0.00341055 | 0.00898592 | 0.00557537 | interior / interior |
| bias1_profiled_removal | gyro_bias_z | deg/hour | 1 | 1 | 0 | upper / upper |
| bias1_profiled_removal | accel_bias_z | m/s2 | -0.00663631 | 0.0325003 | 0.0391367 | interior / interior |
| bias1_profiled_removal | gyro_gain_x | % | -0.02325 | 0.397304 | 0.420554 | interior / interior |
| bias1_profiled_removal | gyro_gain_y | % | -0.143765 | 0.248257 | 0.392023 | interior / interior |
| bias1_profiled_removal | gyro_gain_z | % | -2 | -2 | 0 | lower / lower |
| bias1_profiled_removal | gravity_delta | m/s2 | -0.05 | -0.00995147 | 0.0400485 | lower / interior |
| bias1_profiled_removal | time_offset | s | 0.00341055 | 0.00905022 | 0.00563968 | interior / interior |
| bias1_profiled_removal | earth_removal | fraction | 5.55112e-17 | 3.77476e-15 | 3.71925e-15 | lower / lower |

[Every matched parameter](parameter-changes.csv) and [fit comparison](fit-comparisons.csv) preserve the complete changes for all three models.

## The Z-axis question remains

Rotating-globe Z gain stays at **−2%** and its constant offset stays at **+1°/hour** in both clocks and both processing cases. These are permitted correction limits, not measured instrument drift. The model corrects a logged rate as `(logged rate − offset) / (1 + gain)`. At those limits the multiplier is 1.020408 and the additive correction is −1.020408°/hour. [Z correction coefficients](z-corrections.csv) make the sign convention explicit.

On a stretch with limited rotation-rate variation, gain and offset can compensate for one another. This algebraic possibility does not prove that it explains these fits; the saved singular values alone do not identify which parameters are coupled. Stable ranking across clocks settles this control’s timing sensitivity, but does not settle why Z calibration remains at a limit.

## Calibration comparison

The [calibration plan](CALIBRATION_PLAN.md) tests each Z correction separately by fixing it to zero while leaving the other free. Zero is a diagnostic reference, not an asserted factory calibration. No limits are widened and no time-varying drift is introduced. All three models receive the same changes.

This audit makes **zero native predictions and zero optimizer starts**. It verifies published evidence and completion hashes, and checks matched identities, physical parameter values, limits and convergence labels. Original results remain frozen. The [separate calibration study](../ilvis0-calibration-trial-20261011/README.md) has completed its 12-fit allowance, with 11 fits converged; this audit adds no fits.

## Reproduce

```sh
env PYTHONPATH=analysis ~/venv/bin/python docs/ilvis0-clock-calibration-audit-20261011/build_report.py
```
