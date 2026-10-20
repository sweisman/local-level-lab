# How the measurement works

An **IMU (inertial measurement unit)** contains gyroscopes and accelerometers.
The central observation for the curvature question is the **gyroscope record of
the aircraft's turning**. GPS supplies the route and timing needed to interpret
that motion. The analysis also uses acceleration and receiver-position constraints.

[Current findings](CURRENT_STATUS.md) · [Studies and what they added](STUDIES.md) ·
[All 53 stretches](ilvis0-current-findings-20261015/STRETCHES.md) ·
[Comprehensive CSV](ilvis0-current-findings-20261015/stretch-analytics.csv).

## Primary: NASA airborne analysis

### What each input contributes

| Input | Role |
|---|---|
| Gyroscope angle increments | The recorded turning being investigated; retained as measurements rather than replaced with the finished navigation solution. |
| Accelerometer velocity increments | The force measurements used with the gyros to reconstruct motion. |
| GPS receiver positions and times | Locate the route and constrain the reconstructed track; support speed and interval selection. |
| WGS84 and the alternative disc metric | Declared ways to interpret coordinates under each candidate, not additional instrument observations. |

The gyroscope is the central measurement of interest; this does not establish a
numerical percentage of the evidence attributable to it. The current objective
fits integrated IMU motion against receiver positions. The completed descriptive
[measurement-channel checks](NEXT_STEPS.md#then-strengthen-the-interpretation)
test reduced observations; calibrated attribution remains open.

### The physical prediction

On a globe, an aircraft following local level changes orientation as it travels:
the direction of down changes along the surface. At 900 km/h, the curvature term
is about eight degrees per hour. Aircraft maneuvers and any background rotation
field contribute additional angular motion.

The analysis integrates recorded angle and velocity increments to reconstruct a
trajectory under each model, then compares that trajectory with receiver positions.
It adjusts instrument and initial-motion parameters within the same declared bounds
for every model. The best model is the one that reproduces the observations most
closely after those adjustments pass numerical checks.

| Candidate | Contributions included |
|---|---|
| Globe with the specified background field | Curved surface, aircraft motion and a standard geographic angular-rate field. |
| Globe with zero background field | Curved surface and aircraft motion. |
| Stationary flat disc | Its declared flat geometry and aircraft motion, including changes of direction around the disc. |

The historical names “rotating globe” and “still globe” identify the first two
candidates. They specify a field term; they do not determine its physical cause.

### Selection and comparison

1. **Check the measurements.** Preserve originals, integer increments and timestamps;
   reject invalid packets, checksums and truncation without silently repairing data.
2. **Select stretches before fitting.** Require four continuous minutes, every
   supported receiver speed at least 700 km/h, and the frozen motion, completeness
   and configuration rules. The [eligibility record](ilvis0-highspeed-segments-20261008/ELIGIBILITY.md)
   preserves the exact intervals and every file outcome.
3. **Fit each complete stretch.** Use the same observations for all three candidates.
   Gaps or configuration changes split intervals. Shorter residual sections are
   consistency checks at the same parameters, not extra independent trials.
4. **Test both processing cases.** Allow either no upstream background-field removal
   or an unknown common removed fraction. Both allow constant gyro offsets of
   ±1 degree/hour; that is an assumed error allowance, not a measured drift specification.
5. **Check numerical completion and repeatability.** All required models, processing
   cases, scheduled repeats and controls must pass. A failed fit keeps the comparison
   unresolved even when its last cost leans strongly toward one model.
6. **Interpret shape first.** Compare the disc with the better globe fit. Only after
   both processing cases favor globe is the background-field comparison reported.

### What is independent, and what still needs checking

The fitted IMU increments come from Applanix Group 4; receiver positions come from
Group 10001. Group 1 is the combined navigation solution. It supplies decoder checks
and motion screening, never fitted position or gyro evidence. The
[archive guide](ILVIS0.md#measurement-provenance-and-independence) documents those roles.

GPS is a positioning system; WGS84 is the geodetic reference used for its reported
coordinates. GPS latitude, longitude and height use those conventions. Each candidate assigns
its declared geometry to those coordinates. Separate recorded streams therefore
avoid fitting the finished navigation answer against itself, but do not make the
comparison free of coordinate assumptions. Channel and coordinate checks
test what the inertial observations add.

Two reduced-observation checks address different dependencies:

- **Remove the height score.** One IMU8 comparison passes all repeats and still
  favors globe; the IMU21 sensitivity remains unresolved. Unscored vertical paths
  can become implausible, so this is not a full altitude-independent reconstruction.
  [Height sensitivity](ilvis0-horizontal-multistart-20261019/INTERPRETATION.md).
- **Remove gyro information from a necessary force-magnitude constraint.**
  Permitted calibration and error assumptions leave every candidate overlapping
  in 144 snapshot cases and across 763 packet groups. This reduced observation
  does not distinguish the models, but does not establish a complete feasible
  gyro-free trajectory either. [Whole-history assessment](ilvis0-channel-history-v2-20261019/INTERPRETATION.md).

Fused attitude cannot replace an omitted gyro stream, and omitted acceleration
cannot still supply initial tilt. The [study index](STUDIES.md) records the
independent trajectory, timing, averaging and calibration controls behind those checks.

The [raw gyro companion](ilvis0-gyro-companion-v2/INTERPRETATION.md) compares all
53 pitch-axis means directly with geographic predictions, without fitting gyro
corrections. It assumes level attitude and heading along each candidate's ground
course for the reference plot; 243 fixed orientation/processing scenarios per
stretch expose sensitivity. Aircraft pitching and instrument/mounting effects
remain in the differences. This is a descriptive check of the observed variation,
not a replacement for the full trajectory comparison.

The next prediction method must account for nuisance uncertainty and correlated
receiver errors. Short mathematical controls and the shared-scale calculation
pass, but the first [recording-scale bounds](ilvis0-recording-scale-bounds/INTERPRETATION.md)
are too wide to supply useful intervals. New fitted prediction trials remain
blocked while that method is refined. A [shared reference](ilvis0-shared-reference-scale/INTERPRETATION.md)
keeps candidates from independently inflating their error scales; its Gaussian
covariance assumptions still require observational assessment.

One refinement preserves calibration errors that affect every measurement time
together. For example, an uncertain initial mounting offset is one common
offset, not a fresh error at each later GPS fix. The
[native controls](ilvis0-shared-native-controls/INTERPRETATION.md) and
[joint-interface controls](ilvis0-shared-envelope-controls/INTERPRETATION.md)
check that shared structure while retaining every original physical calibration
direction. Whether the resulting prediction ranges are narrow enough is tested
separately; software correctness alone cannot establish aircraft accuracy.
The [short comparison](ilvis0-acceleration-cover/INTERPRETATION.md) reduces
generated 1.8-second prediction widths to 0.061–0.358 m. The later
[7.2-second comparison](ilvis0-product-prediction/INTERPRETATION.md) preserves
the physical bounds and passes all 48 correctness checks, with widths of about
0.21–1.63 m. Two of six groups still miss the fixed improvement target.
Useful ranges over flight-length intervals and actual aircraft coverage remain
separate requirements.

A [training-only acceleration projection](ilvis0-acceleration-projection/INTERPRETATION.md)
reduces the allowed acceleration-change radius by about 92–93% in six generated
cases. It preserves relationships between calibration terms that separate
coordinate ranges lose. Six [propagation controls](ilvis0-conditioned-native-controls/INTERPRETATION.md)
passed without changing predictions or derivatives. The complete sector comparison
now passes four groups' width targets; these checks do not yet establish narrower aircraft predictions.

A [saved-error audit](ilvis0-saved-prediction-comparison/INTERPRETATION.md)
checks existing retrospective predictions without new fits. Across three fully
completed settings on one recording, horizontal RMS during the withheld interval
is about 2.4 m for the specified-field globe, 143–161 m for zero-field globe and
166–255 m for flat disc. The weaker models already fit the training positions
less closely; the advantage persists after later GPS positions are withheld.
All 18 saved analyses and their original stopping labels remain available.
This adds no independent flight or calibrated absolute-adequacy result.

A completed fit means the numerical search passed its checks; it does not mean the
fit is good. Fit quality, prediction on unused observations, correlated errors and
shared-flight dependence need separate assessment. Statistical significance has not
yet been calibrated. Recorded increments also do not establish that onboard
calibration, filtering or subtraction was absent. IMU8 and IMU21 conversions remain
separately documented rather than treated as interchangeable hardware identities.

Earth’s shape, a retained rotation field and the field’s cause are separate
questions. A globe finding does not establish heliocentrism or exclude geocentric
globe models. The zero-field globe is not a test of every proposed stationary-Earth
explanation. The [rotation-field study](ROTATION_FIELD.md) will estimate the field
freely before interpreting it; fixed-rate fits cannot measure a solar-versus-sidereal
difference. [Next steps](NEXT_STEPS.md) lists the remaining checks.

## Secondary: stationary crowdsourced measurements

Put an IMU on a solid, level support. Record with a marked horizontal axis approximately
toward true north, reverse it 180° with the same face up, and record again. A geographic
horizontal rate reverses sign in sensor coordinates; a constant sensor offset does
not. Repeated A–B–B–A blocks also help separate a linear offset change.

Estimate the signed reversal rate without supplying latitude or an expected angular
rate. A later geographic study would compare sealed estimates with cos(latitude),
fitting the amplitude freely. This tests the horizontal rotation field; it does not
establish Earth’s shape or the field’s cause by itself.

The app and preliminary analyzer are implemented. Physical noise, temperature,
alignment, changing drift and uncertainty still need validation; the implemented
report abstains from scientific decisions. See the [ground method](STATIONARY.md),
[participant protocol](PROTOCOL.md) and [bench checks](BENCH.md).

## Separate evidence, shared principles

Preserve failures, select by recording quality, compare models fairly, measure
uncertainty and account for repeated observations. NASA archive results do not certify
consumer sensors. The [study index](STUDIES.md) records what each investigation added;
[planned work](NEXT_STEPS.md) separates finished results from future analyses.
