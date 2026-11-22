# Fresh-seed changing-gyro-bias pilot

## Fixed question

Does the separate 15-state law cover later errors from the independent
generated IMU/receiver path when its process scales are fixed from declared
generator amplitudes? This is a development stress check. It does not
calibrate aircraft coverage or decide an Earth model. The first pilot's
eight seeds and results remain untouched.

## Fixed cases and work limit

Use seeds `2026111700` through `2026111715`, alternating vibration on even
seeds. Each case has 120 seconds at 100 IMU packets per second and 121
one-second receiver reports. Condition on reports 0–60; seal the forecast;
then score reports 61–120. Supply the true initial inertial state. Use one
worker and one numerical thread, at most 12,000 IMU packets and 121 receiver
reports per case, no native call and no Earth-model fit. The original study
wall allowance is 20 minutes. Each task has one original start. Require a
separately frozen, tested unfinished-task recovery route before launch;
completed technical and numerical failures remain sealed.

## Fixed candidate scales

White acceleration intensity is `(0.01² + 0.02²) / 100`.
White jerk intensity is `0.0003² + 9.80665² × (0.0001² + 0.0002²) / 100`.
White snap intensity is `9.80665² × (2e-6)²`, approximating the generator's
gyro-bias random walk through gravity projection. Receiver random-walk
intensity is `0.01²`; receiver white standard deviation is 0.03 m; initial
receiver-offset standard deviation is 0.01 m. Initial inertial uncertainty
is zero because truth is supplied. These scales are fixed before any new
case is scored. The model still omits detailed attitude geometry and
cross-axis correlations.

## Scores and interpretation

Save the earlier-only mean and standard deviation before scoring later
receiver values. For each complete case retain the later residuals,
standardized errors, fraction of coordinates within marginal 95% ranges,
and the maximum absolute standardized error. The predeclared conservative
simultaneous 95% bound is `3.6351881983520586` standard deviations,
obtained by Bonferroni across 60 later epochs × 3 coordinates × 2 tails.
Count each whole generated history once. Technical completion only requires
the frozen calculation and saved results; no coverage pass is inferred from
16 cases. Any miss stays recorded. A larger independent calibration and
validation design is needed before an observed-aircraft range can be claimed.

All seven reserved ESA groups stay closed. Do not read aircraft originals
or change a frozen source, seed, scale or acceptance rule after launch.
