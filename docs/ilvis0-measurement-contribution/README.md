# What each measurement contributes

All 53 selected stretches have complete full-position model comparisons favoring
the globe. This investigation asks which measured combinations create that
separation and how it changes when particular receiver constraints are removed.

An **IMU (inertial measurement unit)** records turning with gyroscopes and
acceleration with accelerometers. Recorded gyro increments drive reconstructed
attitude; that attitude turns measured acceleration into a predicted trajectory.
Receiver positions constrain the fit. No separate score simply rewards an
expected Earth-rate gyro value. [Measurement dependencies](SOURCE_AUDIT.md)
documents the full path, including initialization and selection.

## Removing height from the score

The [saved-parameter comparison](../ilvis0-receiver-projection-20261018/README.md)
checked eighteen stretches with all six saved primary artifacts available. At
their existing parameters, every one of 36 horizontal-only processing-case
comparisons favors globe. Height-only scoring gives 28 globe and eight flat
rankings. No parameters were refitted in that check.

The [first horizontal-only refit study](../ilvis0-horizontal-observed-20261018/README.md)
then used the shortest artifact-complete stretch from each IMU configuration.
Selection used duration and configuration, not model scores. All twelve baseline
reconstruction checks and all 24 individual fits passed; the study used 1,112
native calls and took 3.64 hours.

| Stretch | Duration | Passed independent repeats | Matched result |
|---|---:|---:|---|
| IMU8 | 9.75 min | 6/6 | Globe preferred under both processing cases. |
| IMU21 | 4.07 min | 3/6 | Unresolved at repeat precision; both starts rank specified-field globe first. |

For the complete IMU8 comparison, specified-field globe horizontal RMS is about
0.37 m, versus 34 m for unsubtracted flat and 17 m with profiled removal. The
zero-field globe is about 7.6 m. The preference therefore persists after
horizontal-only refitting; the background-field comparison also favors the
specified-field model. Its cause and freely measured rate remain separate questions.

The shorter IMU21 stretch has about 1.4 cm horizontal RMS for specified-field
globe, 30 cm for zero-field globe and 9–17 m for flat. Three repeat failures
withhold its matched interpretation. They are not equal model support.
[Detailed results, tracks and metrics](../ilvis0-horizontal-repeat-audit-20261019/INTERPRETATION.md).

## Limits exposed by this check

The unscored vertical paths drift far from receiver altitude: height RMS ranges
from about 0.65 to 114 km across returned fits. These are fitted errors, not
measured aircraft altitude changes. Removing the vertical constraint permits
poorly identified nuisance directions and implausible full trajectories.

Heights remain in initialization, covariance and propagation. Both IMU channels
and conventional receiver coordinates remain. This tests sensitivity to the
scored height constraint; it does not establish altitude/datum independence,
isolate gyro evidence or demonstrate adequate full-flight predictions. The
existing 53-stretch full-position findings stay unchanged.

## Current diagnosis

The [saved-fit audit](../ilvis0-horizontal-repeat-audit-20261019/README.md)
reviewed all 24 endpoints and twelve pairs without original reads or native
predictions. Two zero-field globe pairs settle about 19 ms apart in timing. The
unsubtracted flat pair agrees in cost but misses the 1 mm prediction-RMS limit
by about 0.2 mm. Ordinary and range-scaled affine corrections agree closely;
rescaling alone does not explain the failures.

The completed [28-point diagnostic](../ilvis0-horizontal-repeat-probes-20261019/INTERPRETATION.md)
reproduced every endpoint. Swapping only timing moves horizontal predictions by
4.43 m; the complete parameter midpoint moves them by about 4 mm. The flat
gravity swap changes height by 669 m without changing the horizontal score.
These checks identify coupled timing/calibration and unobserved vertical freedom.

The completed [29-point timing check](../ilvis0-horizontal-timing-path-20261019/DIAGNOSIS.md)
finds derivative differences of 0.008–0.015% in vector norm without crossing a
nominal boundary. The full parameter path is consistent with different locally
stationary solutions. Neither diagnostic performs optimization or relabeling.

The [matched timing search](../ilvis0-horizontal-multistart-20261019/INTERPRETATION.md)
is also complete: 38 starts, 2,376 native calls and 6.59 hours. Both controls and
37 individual fits passed, but only two of six selected repeat comparisons
passed. Specified-field globe reproduced its best predictions; the zero-field
and flat candidates did not. The IMU21 sensitivity result remains unresolved.
Widening that search is deferred in favor of defining the channel-removal controls.

## What remains

- Preserve the [completed timing-search results](../ilvis0-horizontal-multistart-20261019/README.md),
  [all attempts](../ilvis0-horizontal-multistart-20261019/DETAILS.md) and
  [calibration CSV](../ilvis0-horizontal-multistart-20261019/attempts.csv).
- Develop gyro/acceleration contribution controls with explicit replacement
  constraints; fused navigation cannot replace a removed observation stream.
- Test held-out predictions, residual uncertainty and shared-flight dependence.
- Preserve the [artifact inventory](../ilvis0-contribution-inventory-20261018/COVERAGE.md):
  164 ready primaries, eighteen complete six-fit sets. Trace twenty saved-time
  gaps and one unresolved reference separately without replacing historical fits.

The projection adapter passed nineteen constructed checks using correct marginal
covariance and every nuisance column. The subsequent solver studies preserve
their failed stages and completed horizontal-only qualification; height-only
refitting remains unqualified. [Study history](../STUDIES.md).

[Detailed scope](PLAN.md) · [Current full-position findings](../CURRENT_STATUS.md) ·
[Next analyses](../NEXT_STEPS.md).
