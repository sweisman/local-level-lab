# Before an ESA selection revision

Preserve the zero-eligible version-1 inventory and this completed diagnostic.
The position-based method is more useful, but a sparse set of quiet trends
cannot establish a qualifying long flight interval.

1. Specify what motion the future adapter can handle and what selection must
   exclude. A window trend and instantaneous course rate are different targets.
   Either justify a bound on the omitted motion or qualify the complete motion
   treatment; do not silently equate them.
2. Assess receiver-error assumptions without treating the same receiver's
   position/velocity agreement or fitted residuals as independent calibration.
   Retain temporal-correlation sensitivity and the observed unsupported cases.
3. Only after that, freeze a revised receiver-only policy and a finite complete
   inventory. Screen every required support interval; do not interpolate the
   gaps between the 2,048 sampled centers or promote the 96 trend checks into
   selected stretches. Do not examine model outcomes to choose a policy.

Recording 187 remains the development group. Model fitting on other ESA groups
requires the separately frozen confirmation method and identities. No raw-IMU
or model-fitting allowance follows from this diagnostic.

The primary next implementation returns to V01's coupled-calibration prediction
method, described in the [calibration-map follow-up](../ilvis0-calibration-map-diagnostic/NEXT_PLAN.md).
ESA adapter and receiver-error qualification can proceed independently when ready.
