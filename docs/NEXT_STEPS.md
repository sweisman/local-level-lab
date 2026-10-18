# What comes next

The current analysis favors a globe in all 53 selected comparisons. The next work
will establish more precisely what the measurements reveal and how reliably
the fitted models predict new data.
The [verified status](CURRENT_STATUS.md) gives the published totals; the
[study index](STUDIES.md) explains the completed work.

An **IMU (inertial measurement unit)** records turning and acceleration. The archive
analysis uses its recorded increments together with GPS receiver positions.

## Numerical recovery is complete

All **53 selected stretches** now pass their required model comparisons and favor
the globe under both processing assumptions. The original run completed twelve;
all 41 formerly unfinished comparisons now have separately checked recoveries.
Each stretch counts once. The final [complete review](ilvis0-last-review-20261018/README.md)
verified six primary model/case fits, four required repeat pairs and two fresh
controls using saved evidence only.

The last failure concerned fitting across closely spaced packet-timing boundaries.
Two-sided checks resolved it without changing the observations, selected interval,
physical bounds or final native acceptance limits. Failed smooth fits and
conditional timing profiles remain in the history. No recovery worker is active,
and no completed allowance is reopened.

Numerical completion answers whether the declared comparisons have passed their
calculation checks. The next studies establish which measurements drive the
separation and whether the fitted models predict observations outside training.

## Then: strengthen the interpretation

| Analysis | What it adds |
|---|---|
| Separate gyro, acceleration and coordinate contributions | Isolates what the central gyro observations add, using matched tests of gyro input, acceleration input, horizontal-only receiver constraints and coordinate/height assumptions. |
| Residual correlation and calibrated uncertainty | Checks how errors persist over time and how that affects confidence in a model comparison. |
| Prediction on unused observations | Fits instrument parameters on one part of a recording and tests the resulting prediction on a separate part. |
| Shared-flight and instrument grouping | Accounts for simultaneous recorders and repeated stretches from the same flight instead of treating them as independent replications. |
| Additional independent-flight checks | Tests whether the finding transfers across distinct recordings and installations. |

Existing timing, calibration and prediction studies provide development evidence;
they do not complete every check in this table. Exact device documentation remains
useful supporting work. Its absence does not suspend analysis of survey-grade data.

## Measure the rotation field freely

The [additional-data inventory](external-imu-data/README.md) covers longer ESA/DTU
survey lines and raw Wuhan University IMU/GNSS recordings. Each will have a
separate eligibility policy before model fitting. These sources do not change
the existing study or inherit its calibration assumptions or thresholds.
The [ESA selection proposal](external-imu-data/ELIGIBILITY_PLAN.md) uses longer,
slower stretches and receiver-based motion screening. It is a development plan,
not a frozen eligible cohort or authorization to begin fitting.

The present model comparison tests a specified background angular rate against
zero. The next [rotation-field study](ROTATION_FIELD.md) will estimate the retained
field's size and direction from the observations, with aircraft motion, travel
over the surface and instrument errors handled jointly.

It will ask whether one geographic pattern explains different headings, latitudes,
altitudes, flights and instruments. Longer records may help separate a geographic
field from an offset fixed to an instrument. First, the available track geometry
must show that those quantities can be separated. An unconstrained amount removed
onboard cannot be recovered independently from the field that remains in the log.

### Solar versus sidereal rate

A 24-hour rate is **15.0000 degrees/hour**; a sidereal-day rate is about
**15.0411 degrees/hour**. The difference is only **0.0411 degrees/hour**, or about
0.27%. The current short-stretch comparison fixes the background rate, so it
does not measure this distinction.

A dedicated test would use longer supported records, estimate the rate freely,
and show that timing, gain, instrument offset and shared processing cannot account
for the difference. Adding minutes from overlapping recorders does not create
independent observing time. If the precision is insufficient, the result must
report that limit rather than assign a day length.

Measuring a field and its rate describes the observed angular motion. Identifying
its ultimate physical cause requires predictions that distinguish the proposed
explanations; this analysis does not infer a cosmology from the signal alone.

## Separate ground experiment

The [stationary experiment](STATIONARY.md) will test consumer IMUs on solid supports
with repeated 180° reversals. It needs physical noise, temperature and alignment
checks before geographic pooling or detection claims. The NASA results do not
establish consumer-device sensitivity.

[Study index](STUDIES.md) · [Measurement method](METHODOLOGY.md) ·
[Detailed technical roadmap](ANALYSIS_ROADMAP.md).
