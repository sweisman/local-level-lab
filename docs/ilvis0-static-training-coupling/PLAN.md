# Test calibration relationships before reintegrating a trajectory

The long-record prediction ranges are too wide. The previous saved-data check
narrowed only initial height and clock offsets; it left mounting angles and
sensor calibration individually unconstrained. This comparison tests whether
relationships between those parameters contain information their separate
intervals miss.

Use the same six generated cases: three physical candidates under both recorded
processing assumptions. Compact inputs must retain verified parent, configuration,
reference and training-region hashes. Reconstruct the complete static reference
from start fields, as qualified in the [compatibility check](../ilvis0-static-reference-controls/README.md).
Do not load a packet history, read aircraft recordings or integrate a trajectory.

For each case, compare the full parameter domain with all eight fixed yaw strips
covering that same domain. Keep all 27 physical and 24 shared coordinates, the
original 30 training inequalities, calibration limits, source bindings and
normalization caps. Add 48 necessary constraints from the common nonlinear
calibration map, checked by an independent exact-arithmetic export audit.
Check map values and analytic derivatives at the fixed lower, upper and midpoint
probes before projecting any intervals. Probe agreement is a software check, not
a proof of whole-domain numerical accuracy.

Then bound all 27 physical coordinates and the three reference-acceleration
components using the retained joint constraints. Each linear-program proposal
receives independent exact support verification; unsuccessful proposals retain
their safe box bound. Never discard a yaw part because a numerical solver reports
infeasibility. Report a cover-wide bound only if every part passes, using its
worst acceleration allowance. Preserve all failed identities and charges.

## Frozen limits

There are 54 identities: six cases times one full-domain comparison and eight
yaw parts. Each identity has one reference reconstruction, one map setup, two
interval calculations, one independent coupling audit, three map-value probes,
three analytic Jacobians, 4,176 probe checks, 60 linear-program proposals and
180 exact support reservations. Totals are 3,240 proposals and 9,720 support
checks. No optimizer starts, native integrations or trajectory-bound calls occur.

Use one worker and one numerical thread, a cooperative 3,600-second ceiling,
no retries and no allowance expansion. Expected runtime is a few minutes from
the local controls; the ceiling preserves a finite failure outcome. Every unit
of counted work is reserved before execution in the shared journals. Inputs,
source, environment, selection and allocation are frozen through `lll.studies`.

Passing these checks does not require improvement and does not qualify prediction
ranges. Compare the resulting acceleration allowances with the saved values to
decide whether a separately frozen trajectory-bound study is warranted. The
original width targets, full prediction-period coverage and observational
error-law requirements remain unchanged.

[Prediction requirements](../ilvis0-long-staged-feasibility-v2/V01_GATES.md) ·
[Shared implementation](../../analysis/lll/ilvis0_coupled_prediction.py) ·
[Reproducibility](../REPRODUCIBILITY.md).
