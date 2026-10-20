# Compare the raw pitch trend with geographic predictions

The [raw gyroscope plot](ilvis0-gyro-overview/README.md) shows accumulated
pitch-axis increments without a fitted calibration or GPS subtraction. Its
companion will ask a different question: does the variation between recordings
follow predictions made from their course, speed and latitude?

An **IMU (inertial measurement unit)** measures turning with gyroscopes and
specific force with accelerometers. Here the recorded gyro increments remain
the turning observations. Receiver positions supply the trajectory context for
the predictions; they do not supply a replacement gyro signal.

## A transparent reference prediction

For a level aircraft whose nose follows its ground course, the globe transport
contribution around its right-pointing axis is approximately `-speed/radius`.
The specified background field adds `-Omega*cos(latitude)*sin(course)`.
The flat candidate's transport is a vertical yaw contribution, with no pitch
component under these level-flight assumptions. The exact companion will retain
the declared candidate metrics, rather than use this approximation silently.

This calculation must show its assumptions. Aircraft heading can differ from
ground course, roll and pitch can project yaw onto the recorded pitch axis,
and genuine aircraft pitching remains in the raw sum. A sensitivity envelope
may vary declared attitude/crab assumptions, but cannot call them measured.
Possible upstream field removal is shown separately and equally for candidates.

## Planned output and controls

- Use all 53 saved intervals and their hash-checked gyro bins; keep overlapping
  recorders in their supported shared-track groups.
- Preserve the original raw plot. Add predicted versus observed signed rates
  and accumulated angles, with course, latitude, speed, duration and mount
  provenance available for every point.
- Label an aircraft-motion contribution as unresolved when independent heading
  or attitude is missing. Do not subtract fused Group-1 attitude and then call
  the remainder independent evidence.
- Test north/south and east/west limits, reversed headings, hemisphere changes,
  mount-axis signs, nonzero crab/tilt and processing alternatives using independent
  analytic controls before publishing calculated points.
- Report agreement and disagreement descriptively. A common sign, fitted
  orientation or geographic cluster is not an independent vote or a calibrated
  curvature detection.

Freeze generated controls, data identities and a finite allowance before
execution. No new physical-model fits are needed. This diagnostic does not
replace withheld prediction, uncertainty assessment or the planned free-field
measurement.

[Study index](STUDIES.md) · [Roadmap](ANALYSIS_ROADMAP.md) ·
[Free rotation-field study](ROTATION_FIELD.md).
