# Solver robustness, then recording replication

The saved-error audit is complete and performed no refits. The preferred track's
prediction errors grow after GPS fitting stops. Z gyro gain changes from −2% in
whole-stretch fits to +2% in training-only fits under both processing cases; gravity
correction reaches its limit again. This identifies calibration sensitivity, not
a sensor defect or the cause of the errors. The unfinished flat fit fails the
stationarity criterion by about a factor of 40.

## First: one matched solver experiment

The [analytic screen](SOLVER_SCREEN.md) compared three methods using known optima,
including 27-parameter controls with a condition ratio of 50 million. Both dense
methods passed 24/24; the iterative alternative passed 18/24 and will not advance.
The separate [unit-scale trial](../ilvis0-unit-scale-trial-20261011/PLAN.md) keeps
all scientific inputs unchanged, including the original initialization stage.
Its implemented solver passes 25 focused tests and records missing numerical
diagnostics. The six-fit comparison completed with five converged fits; the flat-disc
fit with upstream removal allowed again exhausted its 200-evaluation cap. Its
[matched report](../ilvis0-unit-scale-trial-20261011/RESULTS.md) is published, and solver
qualification did not pass. No retries or replication fits are authorized.

The [saved solver diagnosis](../ilvis0-solver-diagnosis-20261011/README.md) is now complete.
The unfinished fit passes fresh scaled stationarity but lacks successful termination;
its history records only one final stable callback. Calibration boundaries persist.
The [verified-stopping candidate](../ilvis0-solver-diagnosis-20261011/STOPPING_PLAN.md)
passed 24 known-optimum recovery controls and focused false-stop/budget checks. The
[six-fit matched comparison](../ilvis0-verified-stop-trial-20261011/RESULTS.md)
completed with five converged fits; qualification did not pass. The
[saved failure diagnosis](../ilvis0-verified-stop-diagnosis-20261011/README.md) shows
that the bounded linear correction exceeded the residual-step limit by a factor
of 1.55 despite tiny gradient and cost change. The fresh nonlinear probe was not
attempted. No threshold is loosened and no saved failure is relabeled.
Do not advance either revision to replication. The next work follows the
[clock/calibration and numerical-control plan](../ILVIS0_DIAGNOSTIC_PLAN.md),
with fresh observed comparisons requiring a separately prepared finite allowance.

The [clock audit and physical controls](../ilvis0-clock-audit-20261011/README.md)
are complete with no observed fits. Both selected UTC series accumulate about 22 ppm
relative to nominal timing. Scalar controls exhibit clock/gravity coupling and a
gyro gain/offset/clock ambiguity. They do not qualify the full archival solver or
identify its compensation path. The [coupled physical controls](../ilvis0-coupled-controls-20261011/README.md)
now recover known three-dimensional motion and expose the importance of independent
receiver time tags. The separate
[geographic controls](../ilvis0-geographic-controls-20261011/README.md) exercise the
native geographic fitter, off-packet receiver association and nonlinear optimization
with six free parameters for all three true models. Full nuisance freedom and long
record conditioning remain to be qualified. These controls do not authorize recording
replication.

All 24 geographic controls passed their numerical prediction checks, but the
[saved calibration audit](../ilvis0-geographic-controls-20261011/CALIBRATION.md) finds
poor Z gyro-offset recovery and a very weak tangent direction. The
[interval comparison](../ilvis0-interval-controls-20261011/FINDINGS.md) is now complete:
all nine new fits passed, with roughly fourfold error reduction when the interval is
halved and substantially better recovery under added roll. The
[original-rate correction comparison](../ilvis0-compensation-controls-20261011/FINDINGS.md)
has now passed all nine new fits. Combined corrections recover the known offset
within 0.000011°/hour for the globe controls and 0.000377°/hour for the disc control;
the geometry's weak calibration direction remains. The
[latitude/convention extension](../ilvis0-latitude-controls-20261011/FINDINGS.md)
passes all 24 fits with offset error below 0.00079°/hour and no calibration limits
reached. Already-compensated controls expose double-correction error. The
[six-fit observed launcher](../ilvis0-integration-trial-20261011/PLAN.md)
is implemented and requires a separate six-start finite allowance before launch. The
[full-column derivative check](../ilvis0-latitude-controls-20261011/DERIVATIVES.md)
has passed for all three candidates without new optimizer starts.
The proposal authorizes no observed starts. Do not interpret
prediction agreement as recovered calibration or advance the failed observed solver
trial to replication.

Review numerical completion, objective agreement and calibration behavior before
any wider use. A solver that finishes more fits without a stable fit comparison is
not sufficient. Do not widen physical limits or introduce flexible drift to improve
the preferred result. Coordinate/height sensitivity remains a separate later test.

## Second: predeclared retrospective replication

`replication-selection.csv` saves two existing eligible intervals selected only
from the public receiver-based inventory, without reading their model fits. The
rule is: IMU type 21, time-types code 2, filename stream token
`_610_LVIS_38614965.013`, duration at least 420 seconds, excluding the current
control date (2015-10-05) and earlier diagnostic date (2015-10-25). Choose the
earliest and latest remaining dates, then the earliest interval on each date.
These restrictions retain the tested decoding/time convention and enough training
duration; they do not establish a particular physical instrument identity.

The selected dates are 2015-09-24 and 2015-10-22. Each uses its entire previously
eligible interval and the same first-two-thirds training split, with continuous
prediction over the remainder. Exact split epochs, native support and a numerical
freeze must be prepared before requesting its compute allowance. All three models
and both processing cases would require 12 starts, capped at 200 evaluations each,
with no retries. This proposal authorizes none of those starts.

The whole archive was explored previously. These are new prediction checks on
different recordings, not unseen-data confirmation. Distinct dates do not prove
independent instruments or installations. Do not count overlapping streams or
sections as independent flights; do not pool installation calibration merely from
the filename token. Retain failures and report each recording separately.

Use whichever solver has been qualified by the preceding matched experiment.
Predeclare the same criteria, physical limits and covariance for every candidate;
do not choose a solver separately by model or by whichever prediction looks best.
Preserve full-stretch results unchanged. Shape comes first, with rotation withheld
for incomplete or inconsistent shape comparisons. Independent significance and
absolute-fit calibration remain future work.
