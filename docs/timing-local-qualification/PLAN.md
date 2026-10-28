# Keep timing verification local

## Why this is the next test

The [four native regressions](timing-optimizer-regression/INTERPRETATION.md)
did not qualify. All original input bindings replayed exactly, and their
later-position errors remained within the declared screens. Numerical
verification still failed. In the passing-control examples, the failed timing
cell used an anchor about 1.67 milliseconds from the fitted offset—farther than
the 0.1–10 microsecond perturbations in the earlier successful proposal study.

The current method chooses a cell midpoint. That can move the linearization
away from the point whose stability is being checked. A curved timing objective
is missing from the completed analytical control table. These observations
motivate a specific software hypothesis, not a relaxed acceptance threshold.

## Independent control before changing code

Use the known objective with residual vector
`[1, 0.001 × (x + x³)]`, on `−1 ≤ x ≤ 1`. Its exact global minimum is at
`x = 0`, with cost 1. The derivative is stated independently as
`[0, 0.001 × (1 + 3x²)]`.

Check both timing cells. Compare midpoint anchors with anchors obtained by
projecting the original fitted timing value into each cell. The latter means
the nearest feasible point, not a choice based on measured cost. Show which
original cost, stationarity and physical-change screens pass. Limit this
diagnostic to two deterministic cases, four linear operations and twelve
analytical residual evaluations, with no native calls or fits.

## Candidate change and qualification

The independent smooth control supports local anchors, but ordinary regression
tests reject projection alone: five sharp-minimum tests fail when the anchor
lands exactly on the corner. This candidate was rejected before a study freeze.

Use the midpoint of each cell's intersection with the existing ±10-microsecond
neighborhood instead. This samples both sides locally rather than choosing a
far cell midpoint or reusing a derivative at the corner. If a cell has no
representable overlap, use its nearest feasible point; retain singleton cells.
Record the clipped interval and whether the anchor is interior. Preserve every
distinct dispatch transition, singleton cell and nuisance column. Record the
actual anchor policy and anchor coordinates. Do not move timestamps or merge
nearby transitions.

Keep all existing thresholds: cost 10⁻⁸, stationarity 10⁻⁴, position RMS
1 millimetre and maximum 1 centimetre. Keep actual fresh evaluations and the
original extra stationarity requirement. No rejected cell may be omitted.

Qualify a separate version using the original eight analytical objective
families plus the new curved timing objective, each at four declared starts,
and the original eight direct controls. Freeze the exact table, source and
environment before execution. The new ceiling is **36 fits at 200 evaluations
plus eight direct checks at 36**: at most **7,488 analytical evaluations** and
**22,500 bounded linear operations**, 100 iterations each, one numerical thread
and ten minutes. All previous allowances remain closed.

Reuse shared controls, accounting, evaluator and publication components;
preserve the earlier definitions and failed reports. Do not copy a worker tree.
Only a successful complete analytical qualification permits preparation of a
new, separately frozen four-case native regression under the original native
work limits. The 48-case matrix remains blocked until that native gate passes.

This plan changes neither the 53-stretch findings nor any prior fit label.
Calibration and protected confirmation observations remain untouched.

[Next analyses](NEXT_STEPS.md) · [Technical roadmap](ANALYSIS_ROADMAP.md).
