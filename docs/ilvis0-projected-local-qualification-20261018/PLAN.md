# Local stability qualification for projected receiver fits

## Reason for a separate candidate

Removing coordinates creates weakly constrained calibration directions. The
previous trust candidate can fit the retained coordinates closely while its
final undamped probe proposes a nearly full-range move in weak parameters.
Such a move can leave the region where the linearization predicts changes.
The completed/active prior studies and their acceptance labels stay unchanged.

This candidate explicitly changes the **probe region**, not the observations,
physical parameter bounds or numerical tolerances. It tests local numerical
stability; it cannot certify a global optimum, unique calibration or absence
of unscored-axis errors. Paired-start prediction checks remain mandatory.

## Defined local gate

Retain all nuisance columns and require the original projected stationarity
limit **0.0001** before probing. Solve the bounded linear correction within
the original feasible box intersected with a radius of **0.001 per normalized
parameter**. This radius matches the larger derivative-check step used in the
endpoint diagnostic; it is a declared numerical neighborhood, not a physical
calibration allowance or sensor-accuracy claim.

Evaluate that correction freshly using native increments. Require the unchanged
relative cost-change limit **1e-8**, fresh stationarity limit **0.0001**, retained
coordinate RMS change **1 mm**, and maximum change **1 cm**. Omitted axes are
explicitly unchecked. Damping or a tiny optimization step cannot replace these
checks. Preserve the complete Jacobian and numerical rank.

## Sequence and finite budget

1. Pass constructed tests covering null directions, active bounds, the original
   stationarity failure, a nonlinear probe that must fail and a known optimum.
2. Wait for the preceding full trust qualification to finish; inspect every
   saved outcome and paired-start result before freezing this separate batch.
3. If still warranted, freeze and run all **24 generated-motion cases**: three
   models × nominal/variable intervals × horizontal/height objectives ×
   zero/opposed starts. No retries. Cap each fit at **160 native tangent calls**
   plus two diagnostic predictions; **3,888 native calls maximum**, four total
   threads and **30 minutes**. No originals or observed-data fits.
4. Require every fit and all twelve paired-start checks to pass under the same
   retained-error/objective/repeatability criteria as the preceding study.
5. Continue to full-calibration/active-bound controls only if that gate passes.
   A failed candidate blocks observed refits. Diagnose saved artifacts without
   reusing a completed allowance or relabeling prior failures.

Freeze exact sources, tests, environment, parents, identities and allowance;
use exclusive locks, pre-call journals and atomic hashed outputs. Preserve
every failed start. The existing 53 globe / 0 flat / 0 unresolved comparisons
are unaffected by software qualification or this changed local probe.
