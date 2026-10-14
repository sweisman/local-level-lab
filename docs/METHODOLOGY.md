# How the two experiments work

An **IMU (inertial measurement unit)** measures turning and acceleration.
Local Level Lab uses those measurements in two ways: professional airborne analysis,
which is primary, and a simpler stationary crowdsourced experiment under development.

## Primary: NASA airborne analysis

An aircraft following local level over a globe gradually changes its orientation as
it moves across the curved surface. The candidate called “rotating globe” adds a standard
background angular-rate term; “still globe” retains curvature without that term.
These are model names, not determinations of the field's physical cause. The specified still flat disc uses
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
globe fits. Report the background-field comparison only after all required fits converge and both processing
cases favor globe. The two primary cases allow constant gyro offsets of ±1 degree/hour
and either no Earth-rate removal or an unknown shared amount removed upstream.
Those limits are analysis assumptions, not verified per-unit drift specifications.

Keep three questions separate: which surface geometry fits, whether a retained background
angular-rate field is needed, and what physically explains that field. Gyros measure
angular motion relative to an inertial reference. A successful field fit does not itself
explain that reference or establish heliocentrism. The zero-field globe does not represent
every theory of a stationary Earth: a theory proposing a nonzero inertial field needs
its own quantitative predictions. Explanations predicting identical measurements cannot
be distinguished with those measurements. The [interpretation policy](ROTATION_FIELD.md#interpretation)
applies to current model comparisons and the proposed freely estimated field alike.

The fit observations come from two separately recorded streams: Group 4 IMU increments
and positions reconstructed from Group 10001 primary-receiver output. Applanix's
[V6 interface specification, section 3.3.2.1](https://asapdata.arc.nasa.gov/share/ASF_Applanix/POSv6_User_ICD.pdf#page=71)
describes Group 10001 as data emitted by the receiver. Group 1 is the combined IMU/GPS
navigation answer; it supplies decoder checks and motion screening, never fitted gyro
or position observations. This establishes a separation of recorded sources, not
statistical independence of every error or proof of every historical receiver's processing.

Receiver coordinates and height conventions still carry geodetic assumptions. The
globe candidate uses WGS84 geometry; the disc uses its declared alternative metric.
Separate streams therefore do not make the comparison independent of all models.
The planned channel and coordinate controls will test whether the separation requires
the observed gyro increments. The [provenance record](ILVIS0.md#measurement-provenance-and-independence)
states the current evidence and limits. Exact device identification remains useful
parallel work rather than a prerequisite for modeling with survey-grade data.

The contribution is a reproducible test of moving-platform measurements under competing
geometries. A first-of-its-kind claim has not been established. Earth's shape is separate
from geocentric or heliocentric explanations; a globe result alone decides neither.

The original first study found twelve complete globe preferences. Completed numerical
recovery adds eighteen, giving **30 globe preferences, none for flat and 23 unresolved stretches**.
Each recovered comparison passed all six primary fits, its scheduled repeat and fresh
controls. The same intervals, measurements and physical assumptions were retained.
Completed comparisons now include both recorded IMU8 and IMU21 configurations; their
conversion scales differ, but the selection and physical comparison rules are the same.
Unfinished calculations do not give the models equal support.
The consistent completed comparisons are a substantial empirical finding. Establishing
a statistical significance level additionally requires validated uncertainty and
accounting for shared flights or instruments; the stretches are not automatically
independent replications. Those checks quantify the finding's strength without
discarding the observed model preferences.
A better relative fit must still be checked for absolute adequacy, numerical stability
and statistical uncertainty. See the [archive guide](ILVIS0.md),
[current findings](ilvis0-position-stability-trial-20261013/FINDINGS.md) and
[analysis roadmap](ANALYSIS_ROADMAP.md).
The [method development record](METHODOLOGY_DEVELOPMENT.md) organizes the completed
timing, calibration, uncertainty and solver checks and explains what each establishes.

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
