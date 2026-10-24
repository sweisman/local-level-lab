# Qualify the wider-precision derivative calculation on known motion

## Question

Does the full wider-precision calculation reproduce independent known aircraft
motion and retain all 27 nuisance derivatives over twenty-minute histories?
This is the next software gate after the saved-point precision diagnostic.
It does not fit an observed recording or qualify a revised solver.

## Unchanged physical controls

Reuse the qualified analytic Cartesian truth generator, sensor/antenna correction
generator, rate-to-increment construction and physical error scoring. Generate
all three candidates, both latitude signs, removal fractions zero and 0.35,
constant and height-dependent gravity, and climbs and descents: **48 identities**.
Each turning history lasts 1,200 seconds and spans 2 km in height. Supply the true
initial state and nonzero calibration, mounting, lever arm and latency corrections.
These are known-answer controls, not estimates of real device errors.

Use the existing qualified parent-compatibility check for the observation helper:
it now also contains independent receiver conversion functions. Verify the five
original physical helper bodies unchanged, together with the original truth and
numerical dependencies. Freeze the current complete source and compatibility
proof; do not waive a changed physical helper or reuse a mismatched source freeze.

Keep the original value kernel unchanged. Check 300 and 600 Hz histories against
independent positions and compare the wider 300 Hz tangent with the original
value calculation. Retain all 27 columns. Derive wider equations from the exact
hash-bound original tangent source, preserving binary64 parameter products,
processing-fraction mapping, packet-clock accumulation, query dispatch and
query fractions. Form coordinate residuals before returning to binary64.

Preserve the prior targets: horizontal and height RMS at most 1 m, maximum
spatial error at most 5 m; the finer maximum must be at most 0.4 times the
coarse maximum plus 0.001 m. Value/tangent disagreement must stay below 0.001 m.
Short independent controls additionally check every derivative against two
finite-difference steps and the original binary64 derivative implementation,
known straight motion, sub-binary64 coordinate changes and receiver-free forecasting.

## Finite execution and evidence

Before preparation, require source/environment-bound passing tests, including
the actual standalone worker loader. Freeze **48 identities, 144 native calls,
2,695,680,000 packet/query work units**, four workers with one numerical thread
each and a cooperative **two-hour ceiling**. There are 96 unchanged value calls
and 48 wider derivative calls. No optimizer starts, original/protected reads,
retries or inherited unused allowances are permitted. Charge before execution.

Construction journals separately bound each identity to 1,080,000 increments
and 1,080,041 generated samples. Keep every failure. Publish only from saved
hash-verified answers, derivatives, physical errors and accounting records;
packaging must not regenerate truth or propagate a trajectory.

Passing qualifies this tested known-correction calculation only. Training-only
calibration estimation and unchanged stopping checks need a separately frozen
matched qualification before any observed solver revision. The original fit
labels, accuracy limits, calibration bounds and seven protected confirmation
groups remain unchanged.

[Previous precision diagnostic](../esa-precision-diagnostic/README.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
