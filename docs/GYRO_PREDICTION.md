# Compare the raw pitch trend with geographic predictions

The [raw gyroscope plot](ilvis0-gyro-overview/README.md) shows accumulated
pitch-axis increments without a fitted calibration or GPS subtraction. The
[completed companion](ilvis0-gyro-companion-v2/INTERPRETATION.md) compares these
rates with predictions made from course, speed and latitude. A
[matched-field comparison](ilvis0-gyro-companion-v2/MATCHED_GROUP_RESULT.md)
gives recording groups equal weight and checks shape while holding the
background field equal for both models.

An **IMU (inertial measurement unit)** measures turning with gyroscopes and
specific force with accelerometers. Here the recorded gyro increments remain
the turning observations. Receiver positions supply the trajectory context for
the predictions; they do not supply a replacement gyro signal.

## A transparent reference prediction

For a level aircraft whose nose follows its ground course, the globe transport
contribution around its right-pointing axis is approximately `-speed/radius`.
The specified background field adds `-Omega*cos(latitude)*sin(course)`.
The flat candidate's transport is a vertical yaw contribution, with no pitch
component under these level-flight assumptions. The companion uses each
model's declared coordinate metric.

This calculation must show its assumptions. Aircraft heading can differ from
ground course, roll and pitch can project yaw onto the recorded pitch axis,
and genuine aircraft pitching remains in the raw sum. A sensitivity envelope
may vary declared attitude/crab assumptions, but cannot call them measured.
Possible upstream field removal is shown separately and equally for candidates.

## What the diagnostic covers

The calculation used 53 saved intervals, tracked overlapping recordings and
passed 48 analytic controls. The saved comparison includes signed rates,
accumulated angles, course, latitude, speed, duration and mounting provenance.
Aircraft motion remains unresolved where there is no independent attitude
measurement. The gyro diagnostics supply descriptive evidence alongside
withheld prediction, uncertainty assessment and the planned free-field study.

[Study index](STUDIES.md) · [Roadmap](ANALYSIS_ROADMAP.md) ·
[Free rotation-field study](ROTATION_FIELD.md).
