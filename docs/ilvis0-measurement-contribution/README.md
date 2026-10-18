# What each measurement contributes

All 53 selected stretches now have complete numerical comparisons favoring the
globe. This next investigation asks which measured combinations create that
separation, and how it changes when specific receiver constraints are removed.

An **IMU (inertial measurement unit)** records turning with gyroscopes and
acceleration with accelerometers. In this analysis, recorded gyro increments
drive the reconstructed attitude; that attitude turns the measured acceleration
into a trajectory. The predicted positions are then compared with the receiver's
recorded positions. There is no separate term that simply rewards an expected
Earth-rate gyro value. [Measurement dependencies](SOURCE_AUDIT.md) explains the
full path, including initialization and selection.

## First software result

The new receiver-coordinate adapter passes **19 known-answer checks**. It can
retain full three-dimensional positions, horizontal positions or heights while
using each selection's correct marginal covariance. It preserves all nuisance
parameter columns, including columns that become unidentifiable after coordinates
are removed.

One control explicitly demonstrates why deleting already-whitened residual rows
can produce the wrong likelihood. Other controls verify derivatives, coordinate
permutations, lost rank and rejection of invalid covariance or saved arrays.
These checks use small constructed matrices, with no original-recording reads,
native predictions or observed-data fits. They do not add an empirical finding.

## First receiver-coordinate result

The [saved-parameter comparison](../ilvis0-receiver-projection-20261018/README.md)
completed **324 projections** for eighteen stretches, covering all three models
and both processing assumptions. At the existing fitted parameters:

| Receiver constraints scored | Globe / flat / tie |
|---|---:|
| Full positions | 36 / 0 / 0 |
| Horizontal positions only | 36 / 0 / 0 |
| Height only | 28 / 8 / 0 |

These are 36 processing-case comparisons on eighteen stretches, not independent
flights. The globe preference persists when height is removed from the score.
Height alone gives mixed rankings. The parameters still come from full-position
fits, so these scores do not establish the best fit attainable after removing
coordinates. Both gyro and acceleration observations remain in use.

The full scores reproduce the saved objectives exactly. Removing coordinates
also makes some nuisance directions unidentifiable: fifty of 108 horizontal
projections and all 108 height-only projections lose numerical rank. Every
parameter column was retained; this rank diagnostic changes no acceptance rule.
[Interpretation and limits](../ilvis0-receiver-projection-20261018/INTERPRETATION.md).

## Refitting qualification

The [refitting qualification](../ilvis0-projected-fitting-controls-20261018/README.md)
has completed its fail-fast batch: **24 controls passed, one failed and eighteen
were not run**. The six horizontal fits reached so far passed; their second-start
checks remain untested. A height-only control exhausted its allowance without
meeting stationarity, despite a very small retained-position error. Omitted
coordinates moved substantially. The candidate remains unqualified and no
observed refit follows from these partial successes.
[What passed and why advancement is blocked](../ilvis0-projected-fitting-controls-20261018/INTERPRETATION.md).

The subsequent [trust-region matrix](../ilvis0-projected-trust-qualification-20261018/README.md)
ran all 24 generated fits. Sixteen fits and eight paired-start comparisons
passed, including every horizontal fit. Its eight failures were height-only
stability probes that made large nonlinear moves through weak directions.
The subsequent local-probe matrix used the same numerical tolerances within an
explicit 0.001 normalized-coordinate neighborhood. It passed all 24 individual
fits but only eleven of twelve paired-start comparisons. The
[larger-budget continuation](../ilvis0-projected-budget-continuation-20261018/PLAN.md)
completed both height-only fits in 1,035 native calls, within its 1,204-call
allowance, but did not resolve that pair's objective disagreement. The
[complete saved review](../ilvis0-projected-complete-review-20261018/README.md)
therefore remains unqualified. Both coordinators finished without launching the
broader full-calibration matrix; they are not waiting or running.
[Call-allowance publication correction](../ilvis0-projected-budget-continuation-20261018/PUBLICATION_NOTE.md).

All twelve predeclared horizontal fits and all six horizontal repeat comparisons
pass. A separate [horizontal-only capability review](../ilvis0-projected-horizontal-review-20261018/README.md)
verifies that entire subset while retaining height-only as unqualified. The current
[full-calibration qualification](../ilvis0-projected-horizontal-fullcal-20261018/PLAN.md)
tests horizontal scoring with all 26/27 nuisance columns: twelve generated fits,
six repeat comparisons and at most 1,944 native calls. It reads no original
recordings and starts no observed-data fits. Success would qualify preparation
of a small matched horizontal-only recorded-data study, not height-only refitting
or calibrated scientific significance.

The [saved-primary inventory](../ilvis0-contribution-inventory-20261018/COVERAGE.md)
is complete. Of 318 final primary fits, 164 have ready residual/Jacobian and
receiver-time artifacts. Eighteen stretches have all six fits ready for a matched
comparison. Other fits lack a declared array, saved time context or a resolvable
reference. These reuse gaps do not change the completed 53/0/0 model result.

1. Preserve the completed inventory and trace the twenty time-context gaps and
   one unresolved artifact reference through saved provenance.
2. Preserve the completed fixed-parameter comparison and its frozen sources;
   do not repeat projections to regenerate documentation.
3. Complete the separately frozen horizontal-only full-calibration controls,
   retaining every column and checking unscored-coordinate effects. Height-only
   qualification remains a separate open problem; preserve the failed repeat check.
4. Only after those controls pass, freeze a small matched horizontal-only observed
   refit study with finite limits, common initialization rules and independent repeats.
5. Develop gyro/acceleration contribution controls with explicit replacement
   constraints, then held-out prediction and calibrated uncertainty.

Removing receiver heights from the objective still leaves heights in the current
initialization, covariance and trajectory context. That experiment measures
sensitivity to a constraint; it does not establish independence from altitude or
the coordinate datum. Likewise, coordinate projections retain both IMU channels
and do not isolate the gyroscope by themselves. No fused navigation attitude or
angular rate may substitute for a removed observation stream.

The existing findings and all frozen studies remain unchanged. No observed
ablation run has started. [Detailed scope](PLAN.md) · [Current findings](../CURRENT_STATUS.md) ·
[Next analyses](../NEXT_STEPS.md).
