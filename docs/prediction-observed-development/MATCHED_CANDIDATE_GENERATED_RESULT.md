# One recording, three candidate models

The [finite generated study](MATCHED_CANDIDATE_GENERATED_PLAN.md) completed
12/12 recordings and 36/36 candidate fits. Every fit converged. For each
recording, rotating globe, stationary globe and stationary disc received the
same generated IMU increments and earlier receiver positions. All three
forecasts and their physical and receiver ranges were saved before later
receiver data were generated.

**The ranges did not distinguish the models.** Each recording had 40 later
receiver positions. For all 12 recordings, those positions fell inside all
three candidate receiver ranges. Every candidate pair's ranges overlapped at
every later position. Shape and background-field comparisons therefore
abstained in all 12 cases.

| Saved receiver-range comparison | Median across the 12 recordings |
|---|---:|
| Rotating-globe mean full horizontal width | 138.4 m |
| Stationary-globe mean full horizontal width | 138.2 m |
| Stationary-disc mean full horizontal width | 131.1 m |
| Rotating-globe vs disc median forecast-center separation | 22.6 m |
| Rotating-globe vs stationary-globe separation | 9.6 m |

The widths are for whole withheld paths, under each candidate's declared
Gaussian error and calibration assumptions. They are much broader than the
typical separation of the forecast centers. The overlap is a property of
these generated routes, noise laws, calibration bounds and 120-second
recordings. It does not show that the physical models are equivalent, and it
does not calibrate uncertainty for real aircraft.

The [saved horizon audit](matched-candidates-horizon-audit.json) shows that
more time within these recordings does not close the gap. At the 40th withheld
position, median rotating-globe-versus-disc center separation is 93 m against
a combined horizontal half-width of 402 m. For rotating versus stationary
globe the figures are 30.5 m and 421.5 m. No pair has disjoint coordinate
ranges at any withheld position.

The [saved width-component audit](matched-candidates-width-components.json)
shows where the broad ranges come from **within this assumed calculation**.
By the 40th position, the calibration component is about 98.4% as large as
the total horizontal half-width; the conditional future-noise radius is only about
3–4 m against a total half-width of about 200–212 m. This does not identify
which individual calibration parameter causes the width or establish actual
aircraft sensor errors.

The [saved calibration audit](matched-candidates-calibration-audit.json)
compares the twelve correct-model fits with their known generated sensor
settings. Their median sensor-setting RMS error is 0.71 of the permitted
parameter half-range. Z-axis gyro bias and timing offset are near their
permitted limits in all twelve fits. The
[independent weak-direction audit](matched-candidates-weak-directions.json)
recomputes the saved training Jacobians: Z-axis gyro bias and vertical
accelerometer bias are among the three largest components of the weakest
local direction in all twelve correct-model fits. These are generated-data
diagnostics of calibration recovery, not measured device drift or a unique
explanation of the later range width.
The same Z-axis gyro-bias weakness appears in the
[saved opened-ESA fit audit](ESA_SAVED_WEAK_DIRECTION_RESULT.md). That is a
single-flight development comparison, not independent replication.

The [verified study report](matched-candidates-full-result.json) records
completion, convergence and containment for every case. The
[saved range audit](matched-candidates-full-range-audit.json) records widths,
center separations and overlap without new fitting. The next step is a
separately frozen geometry and calibration test. It should check whether
different earlier motion can constrain the weak combination without assuming
narrower device bounds. No new observed aircraft group is opened here.
