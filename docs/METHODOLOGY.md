# How the two experiments work

An **IMU (inertial measurement unit)** measures turning and acceleration.
Local Level Lab uses those measurements in two ways: professional airborne analysis,
which is primary, and a simpler stationary crowdsourced experiment under development.

## Primary: NASA airborne analysis

An aircraft following local level over a globe gradually changes its orientation as
it moves across the curved surface. A rotating globe adds a background rotation term;
a still globe retains curvature without that term. The specified still flat disc uses
a different geometry. All three are fitted against the same raw IMU increments and
receiver positions, with the same allowed instrument and motion errors.

The archive selector requires at least four continuous minutes with every supported
ground-speed observation at least 700 km/h, plus frozen completeness, timing and motion
rules. It saves file hashes, exact intervals, durations, speeds and exclusions **before
model fitting**. The [public inventory](ilvis0-highspeed-segments-20261008/ELIGIBILITY.md)
is reused rather than selecting attractive gyro readings.

Fit each complete selected stretch jointly. Fixed shorter sections check residuals at
the same fitted parameters; they are not separate flights or fresh calibration fits.
Gaps and configuration changes split intervals. Joining files needs demonstrated
timing, sample and installation continuity. Whole-stretch fits require credible error
assumptions for their entire duration; residual sections can expose violations but
cannot prove stationarity.

Interpret **globe versus the specified flat disc first**, using the better of the two
globe fits. Report rotation only after all required fits converge and both processing
cases favor globe. The two primary cases allow constant gyro offsets of ±1 degree/hour
and either no Earth-rate removal or an unknown shared amount removed upstream.
Those limits are analysis assumptions, not verified per-unit drift specifications.

The archive contains independent recorded increments and a combined navigation answer.
The latter supplies decoder checks and motion context, never independent Earth-model
evidence. Receiver coordinates, height conventions, possible onboard corrections and
calibration bounds remain explicit assumptions to test. Exact device identification is
useful parallel work rather than a prerequisite for modeling with survey-grade data.

Completed results favor globe in twelve stretches and flat in none; forty-one are
numerically unresolved. Unfinished calculations do not give the models equal support.
A better relative fit must still be checked for absolute adequacy, numerical stability
and statistical uncertainty. See the [archive guide](ILVIS0.md),
[findings](ilvis0-highspeed-segments-20261008/FINDINGS.md) and
[analysis roadmap](ANALYSIS_ROADMAP.md).

## Secondary: stationary crowdsourced measurements

Place an IMU on a solid, level surface. Point a marked horizontal axis approximately
toward true north, then reverse it by 180° with the same face up between still blocks.
A geographic horizontal rate changes sign in sensor coordinates; a constant sensor
offset does not. Repeating A–B–B–A helps separate a linear offset change.

The analyzer estimates the **signed reversal signal first**, without latitude or a
predicted Earth rate. A later population study would compare sealed estimates with
cos(latitude), fitting the amplitude freely and accounting for orientation uncertainty,
instrument, day and site dependence. Horizontal northward rotation has the same sign
in both hemispheres; this is not a primary vertical-rate test.

This measures a rotation field rather than deciding Earth's shape by itself or explaining
the field's ultimate cause. It does not require an aircraft, flight identity, continuous
GPS, turbulence corrections or in-flight reversals.

Consumer slow-rate sensitivity and calibrated uncertainty still need physical controls.
Reversal removes constant offsets, not arbitrary changing drift. Longer averaging cannot
restore a signal erased by firmware or guarantee resolution beneath a fixed digital step.
The implemented output is a preliminary diagnostic and always abstains from a scientific
decision. See the [stationary method](STATIONARY.md), [protocol](PROTOCOL.md) and
[bench checks](BENCH.md).

## Separate evidence, shared principles

Preserve originals and failures; select by recording quality rather than model agreement;
measure uncertainty; replicate across instruments; publish assumptions and exclusions.
NASA observations do not certify consumer sensors. Ground recordings do not inherit
airborne thresholds or imitate permanent aircraft installations.

Earlier passenger-flight methods remain in the [technical methodology history](METHODOLOGY_TECHNICAL.md)
and [aircraft validation history](VALIDATION_AIRCRAFT_HISTORY.md). Frozen studies remain
unchanged. The [rotation-field roadmap](ROTATION_FIELD.md) describes the separate future
airborne field measurement and its interpretation.
