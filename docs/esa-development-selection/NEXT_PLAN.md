# Diagnose receiver-motion screening before revising selection

Version 1 admits no stretches from development recording 187. It excludes
63,488 of 64,080 epochs; the longest surviving run is about 84.5 seconds.
The motion margin covers all 63,488 excluded epochs. Individual failed windows
number 46,285; 16,873 epochs fail speed and 2,954 lack IMU time support. Reasons
overlap. No epoch fails the specified receiver-quality thresholds.

This result does not establish that the aircraft lacks long usable flight
periods. The selector takes the median of absolute adjacent-sample course rates
inside ten-second windows. Real heading corrections and receiver velocity noise
can both increase that quantity. The present inventory does not separate them.

## Next qualification

1. Use independent known-motion controls with realistic sampling, reported
   velocity precision, noise correlation, heading wrap and injected maneuvers.
   Compare the existing adjacent-difference statistic with a predeclared
   ten-second velocity-trend estimate. Test missed maneuvers as well as false
   exclusions; do not simply maximize retained duration.
2. Freeze a bounded receiver-only diagnostic on recording 187. Report north/east
   velocity changes, course-rate estimates, temporal correlation, reported
   velocity covariance and the contribution of climb versus turning. Do not
   inspect gyroscope values or Earth-model outcomes.
3. If a different estimator is justified, publish a new policy and finite freeze
   before calculating a replacement inventory. Preserve version 1, its thresholds,
   sources and every rejection. No policy is changed merely to produce intervals.
4. Qualify sampling phase, lever arms and native rate integration separately.
   Multiplying rates by actual periods is checked arithmetic under an explicit
   right-endpoint hypothesis, not proof of the instrument's integration convention.

Protected confirmation groups remain reserved. A new inventory is not an
authorization to fit those groups or transfer Applanix calibration assumptions.

[Frozen inventory](README.md) · [Selection policy](../external-imu-data/ESA_SELECTION_V1.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
