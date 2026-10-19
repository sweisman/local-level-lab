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

The [measurement-contribution work](ilvis0-measurement-contribution/README.md)
has completed its input audit, saved-fit inventory and first coordinate-subset
comparison. Of 318 primary fits, 164 have reusable saved arrays, including all six
fits for eighteen stretches. At their existing fitted parameters, all **36
horizontal-only processing-case comparisons favor globe**; height-only scoring
gives 28 globe and eight flat preferences. No parameters were refitted. Both gyro
and acceleration observations remain in use, and heights still enter other parts
of the reconstruction.

The staged horizontal-only fitting software is now qualified, including every
generated-model pair. Its earlier failed studies remain preserved in the
[study index](STUDIES.md).

The [first recorded-flight refit study](ilvis0-horizontal-observed-20261018/README.md)
has completed all twelve reconstruction checks and all 24 individual fits in
1,112 native calls, taking 3.64 hours. Its two stretches were selected by duration
and IMU configuration, without model scores.

| Configuration | Duration | Passed repeats | Horizontal-only outcome |
|---|---:|---:|---|
| IMU8 | 9.75 minutes | 6/6 | Globe preferred under both processing cases. |
| IMU21 | 4.07 minutes | 3/6 | Matched result unresolved; both starts rank specified-field globe first. |

The [saved-fit review](ilvis0-horizontal-repeat-audit-20261019/INTERPRETATION.md)
explains the distinction. The two zero-field globe pairs settle about 19 ms apart
in timing; the unsubtracted flat pair misses the prediction-repeat limit by about
0.2 mm. All endpoints pass their individual gates. Changing the affine solve's
coordinate scaling does not resolve the disagreements.

Removing height from the score also permits implausible vertical paths: unscored
height RMS ranges from about 0.65 to 114 km. The completed IMU8 result shows that
the preference survives removing the scored height constraint. It is not a
credible full flight reconstruction or a gyro-only/altitude-independent test.
The original full-position **53 globe / zero flat / zero unresolved** findings
remain unchanged.

The completed [28-point diagnostic](ilvis0-horizontal-repeat-probes-20261019/INTERPRETATION.md)
reproduced every saved endpoint. A timing-only swap changes horizontal positions
by 4.43 m, while the complete parameter midpoint changes them by about 4 mm:
timing and calibration compensate each other. In the flat model, a gravity swap
changes height by 669 m with no horizontal-score change.

The completed [29-point timing check](ilvis0-horizontal-timing-path-20261019/DIAGNOSIS.md)
finds no gross derivative fault: five comparisons differ by 0.008–0.015% in
vector norm, with no integration boundary crossed. The sampled path is consistent
with different locally stationary solutions. It is not an optimized timing profile.
No fit, repeat or scientific labels change from these checks.

The remaining sequence is:

1. The [multi-start controls](ilvis0-multistart-controls-v3-20261019/README.md)
   passed all four known-answer systems in 24 starts /166 constructed calls.
   The separate [matched recorded-data study](ilvis0-horizontal-multistart-20261019/OVERVIEW.md)
   completed 38 starts /2,376 native calls in 6.59 hours. Both controls and 37
   individual fits passed, but only two of six selected repeat comparisons
   passed. The IMU21 sensitivity result remains unresolved; its
   [interpretation and next step](ilvis0-horizontal-multistart-20261019/INTERPRETATION.md)
   defer wider timing searches in favor of channel-contribution controls.
2. Preserve complete and unresolved sensitivity results separately; do not expand
   the cohort merely to obtain more favorable outcomes.
3. Test gyro and acceleration contributions with explicit replacement constraints.
   Coordinate removal alone does not isolate either IMU channel.
4. Establish prediction on unused observations, residual uncertainty and
   shared-flight dependence before calibrated population claims.

Height-only qualification and missing saved-artifact references remain separate
open work. Failed controls retain their original labels.

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
