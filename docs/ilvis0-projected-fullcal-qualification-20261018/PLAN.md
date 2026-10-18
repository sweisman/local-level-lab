# Full-calibration projection controls

## Prerequisite and purpose

Run only after a separately frozen projected-fitting candidate passes its full
generated-motion matrix and paired-start checks. The six-parameter controls do
not by themselves qualify a fit with all 26/27 archival nuisance parameters.
This stage tests that larger interface before any recorded-flight refit.

Reuse the independent twelve-second geographic trajectories and nominal 200 Hz
increments. Keep every observed receiver epoch and every declared nuisance
column. All three physical models must be exercised under fixed-zero and
profiled upstream field-removal hypotheses. The generating removal is zero;
the profiled control therefore includes a true optimum at that parameter bound.

## Fixed matrix to prepare

Three models × two processing cases × horizontal/height objectives × two starts:
**24 generated fits**, with twelve paired-start comparisons. Use the original
`shape.instrument_limits(1.)` bounds, which are analysis assumptions, not measured
per-unit calibration limits. The active layout is 26 or 27 columns exactly.

At the generating point, the six independently injected nuisance values retain
their existing definitions; the other calibration terms are zero. The profiled
removal coordinate is -1, representing zero upstream removal. The first start
sets ordinary nuisance coordinates to zero and removal to -1. The second uses
fixed alternating ±0.02 normalized nuisance coordinates and removal -0.8. Fix
the parameter ordering and these starts before computing any result.

Require fresh numerical checks, retained-coordinate errors below 2 mm, cost no
greater than the independent generating reference plus 0.01, and paired-start
cost/prediction agreement under the preceding qualification's limits. Preserve
rank deficiency and different nuisance estimates; do not discard columns or
claim unique calibration from a small prediction error. Report unscored errors.

## Proposed finite allowance

At most **160 tangent calls per start**, including fresh acceptance checks,
plus two diagnostic predictions: **3,888 generated native calls maximum**,
four total numerical threads, thirty minutes, no retries. Freeze exact sources,
environment, model/case identities, starts and allowance only after prerequisites
pass. There are zero original-recording reads and zero observed-data starts.

No fitting is authorized by this preparation alone. Passing this stage would
allow preparation of a small, separately frozen matched observed refit study;
it would not change the original 53/0/0 results or calibrate scientific evidence.
