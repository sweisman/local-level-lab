# How the measurement works

An **IMU (inertial measurement unit)** contains gyroscopes and accelerometers.
The gyroscopes record angular motion of the aircraft-mounted instrument.
The accelerometers measure specific force, the acceleration the instrument
feels from forces other than gravity. A separate GPS receiver reports the
route, time and speed. The analysis reconstructs motion under each candidate
and tests how well that path accounts for the receiver observations.

[Current findings](CURRENT_STATUS.md) · [Study index](STUDIES.md) · [Flight-stretch table](ilvis0-current-findings-20261015/STRETCHES.md)

## What each instrument contributes

| Input | Role |
| --- | --- |
| Recorded gyro increments | Observed changes in angle from maneuvers, motion over the surface, and any retained background field. |
| Recorded accelerometer increments | Help reconstruct motion from measured specific force. |
| Primary GPS receiver positions and times | Locate the route and constrain the reconstructed path. A forecast reserves later positions for testing. |
| Coordinate reference | The receiver reports latitude, longitude and height in WGS84. Each candidate specifies how those coordinates map to physical distances. |
| Combined IMU/GPS navigation | Used to validate decoding and screen motion. The model comparisons use the recorded increments and primary receiver stream. |

The gyro record is the direct measurement of angular motion. Exactly how much it contributes to the final shape comparison is still under study. In the acceleration-only checks, force does not uniquely determine the aircraft’s orientation. Separate receiver outputs and inertial increments also leave open shared measurement errors and any onboard corrections. [Provenance](ILVIS0.md#measurement-provenance-and-independence) · [Measurement contribution](ilvis0-measurement-contribution/README.md)

## The physical comparison

On a globe, the direction of local down changes as the aircraft moves. For a level path at 900 km/h, the curvature term is about eight degrees per hour. The recorded angular motion also contains aircraft maneuvers and may contain a geographic background field.

| Candidate in the NASA archive study | What the calculation includes |
| --- | --- |
| Globe with the specified background field | Motion over a curved surface and a prescribed geographic angular-rate pattern. |
| Globe with zero background field | Motion over the same curved surface with the field term set to zero. |
| Stationary flat disc | A north-pole-centered disc with a 6,371 km scale, gravity normal to the disc, and zero background field. Following an eastward course changes compass direction around the disc. |

Historical labels “rotating globe” and “still globe” refer to the first two rows. They describe the tested equations. The field's magnitude and direction in the first model are supplied to the calculation. A separate study is needed to estimate them freely or test their physical cause. [Rotation field and interpretation](ROTATION_FIELD.md)

## How the NASA stretches were compared

1. Preserve original records, timestamps, raw increments and checksums. Select complete stretches with four minutes or more of usable data and GPS ground speed of at least 700 km/h throughout. The interval rules include a fused-navigation alignment flag, and all 53 stretches come from files where it was set throughout. Earlier exploratory archive fits preceded this selection, and the same intervals were used throughout the published 53-stretch study. [Selection rules](ilvis0-highspeed-segments-20261008/ELIGIBILITY.md)
2. For each complete stretch, reconstruct the flight under all three candidates. Fit the permitted calibration and starting-motion parameters with the same bounds for each model. Compare both declared processing cases. One assumes no previous field subtraction, the other allows a common fraction to have been removed. For a candidate with no field, that second case adds a rotation of the opposite sign. The ±1°/hour gyro offset is a working allowance per axis, and the only one fitted to these stretches so far. With the globe and its specified field, the level-axis offsets came out near 0.1°/hour and did not change with speed. [Archive guide](ILVIS0.md) · [Review of the saved fits](red-team-20261125/README.md)
3. Verify numerical completion. Compare the lower-cost globe with the specified disc. Compare the two globe field cases after the shape comparison favors globe. When a required fit fails, the corresponding comparison remains unresolved. [Saved numerical results](CURRENT_STATUS.md)
4. Test the interpretation with matched-field forecasts and measurement controls. The original three-model analysis pairs the disc with zero field. Later matched comparisons also give both geometries the same field, to separate the effects of shape and the prescribed field. [Matched NASA forecasts](ilvis0-measurement-contribution/MATCHED_FOUR_GROUP_AUDIT_RESULT.md)

## Reading the results

| Result | Meaning |
| --- | --- |
| Numerical pass | The solver met its stage-specific checks. |
| Lower fitted cost | This candidate describes the recorded inputs more closely under the stated model and corrections. |
| Lower withheld prediction error | A fit to earlier observations predicts later positions more closely than a competing fit. |
| Absolute adequacy | The forecast meets independent position and physical limits for the stated check. |
| Calibrated confidence | The full decision rule has a verified error rate under relevant uncertainty. For aircraft this remains open. |

The withheld-position test fits only earlier positions, then uses recorded IMU motion to predict the later route. NASA results are retrospective development tests on the original archive. The ESA development predictions come from one flight group. The separately reserved groups provide a later confirmation test after the aircraft error model and decision rules are qualified. [Withheld prediction](PREDICTION_VALIDATION.md) · [What comes next](NEXT_STEPS.md)

## Stationary ground measurements

The separate consumer experiment uses a stable, level support. Record with a marked horizontal axis near true north, reverse it 180° with the same face up, and record again. A geographic horizontal rate reverses sign in sensor coordinates, while a constant sensor offset stays fixed. Repeated orientations help separate changing offset from the reversal signal. Estimate the signed rate before comparing it across latitudes. [Ground experiment](STATIONARY.md) · [Participant protocol](PROTOCOL.md)

[Earlier method and control history](METHOD_DEVELOPMENT_HISTORY.md) · [Mathematics](MATH.md)
