# Qualify timing-aware final verification

## Purpose and design

Keep the existing actual-cost trust-region optimizer and its near-zero rule.
Change only how its final local correction is checked near a timing slope
change. The [18 physical proposal checks](saved-timing-cell-native/INTERPRETATION.md)
support this component; they do not qualify the complete fitting path.

## Constraints

Keep every active nuisance coordinate, the physical bounds, the compensated
mean and noise calculation, and the original numerical limits: relative cost
10⁻⁸, stationarity 10⁻⁴, position RMS 1 millimetre and maximum 1 centimetre.
Keep the original stationarity requirement as an additional conservative gate.
Do not accept a boundary merely because it is a boundary.

The native clock adds float64 packet durations and compares receiver time plus
offset with packet end time. Apparently coincident receiver transitions need
not be identical: the four exposed examples have five or six nearby clock
knots spread across about 7 × 10⁻¹⁵ seconds. Preserve these distinctions rather
than silently rounding them into one common boundary.
The rounded native-dispatch preflight resolves eight distinct transition
brackets and nine cells at each of the four saved points. No time is moved.

## Implementation sequence

- [x] Extend `lll.timing_cells.bounded_step` to support a timing coordinate
  fixed by an exact cell constraint, while retaining the complete Jacobian and
  parameter list. Solve the remaining free coordinates and report fixed ones.
  Preserve existing results for strictly open parameter boxes.
- [x] Add `lll.timing_intervals` to enumerate clock-dispatch cells near a fitted
  timing offset. Use the native float64 clock and offset arithmetic. Find
  representable transition brackets by bounded bisection; merge only identical
  brackets. Reject unsupported/unresolvable geometry. Test irregular clocks,
  physical endpoints, closely spaced transitions and complete coverage.
- [x] Add `lll.ilvis0_timing_stop`: repeat the final baseline, then evaluate a
  fixed interior anchor and its full-column bounded proposal in every local
  cell. Use a fixed 10-microsecond neighborhood and at most 16 distinct
  transitions (17 cells). Include the current cell; no best-side selection.
  Reject overflow rather than dropping cells. Keep actual cost and physical
  position checks; retain all failures and full diagnostic records.
- [x] Add explicit optional verifier/reservation hooks to
  `lll.ilvis0_solver_trust_v2`, preserving its default behavior. Reserve 36
  evaluations for final verification: one final baseline, one repeat and at
  most two calls per cell. Charge every linear solve when a counter is supplied.
  Let `lll.ilvis0_near_zero` accept an explicit ordinary-solver provider without
  changing its default. Compose these pieces without copying either optimizer.
- [x] Qualify complete fits and direct non-minimum probes using independently
  specified smooth, kinked, boundary, nonlinear and rank-deficient objectives,
  multiple starts and physical-error controls. Compare default behavior and
  ensure no exhausted budget, omitted cell or failed physical check can pass.

Initial software verification passes 155 tests, including eight complete kinked
fits from different starts. Direct tests retain rejection of a non-minimum,
failed physical checks and points failing the original stationarity threshold.
This is not yet the source-bound analytical qualification below.

## Finite qualification and next gate

Ordinary deterministic tests run through the compute guard with at most four
total numerical threads. Before a durable analytical qualification run, freeze
its exact case table, starts, source/environment hashes and work limits through
`lll.studies`. Its ceiling is 32 fits at 200 evaluations each plus eight direct
checks at 36 evaluations each: at most 6,688 analytical residual evaluations,
zero native calls and zero aircraft observations. Use at most 20,000 bounded
linear solves, 100 iterations each, one worker and a ten-minute cooperative
ceiling. Charge before execution; preserve every failure and close unused work.

The fixed fit cases are an interior optimum, a physical-bound optimum, a
nonlinear optimum, a curved redundant problem, two kink locations, a smooth
timing optimum and a 27-coordinate redundant timing problem. Each uses four
declared starts: zero and alternating-sign vectors of −0.8, +0.6 and +0.9.
Their optimum costs and predicted observations are stated independently of the
fitter. Weak coordinates are judged by prediction recovery, not a unique
calibration vector. Predictions from different starts must agree within twice
their individual declared prediction tolerance; costs use the same pairwise
rule.

The eight direct checks cover two valid kink minima, two non-minima, a sharp
minimum that must still fail the original stationarity gate, a physical-error
failure, a repeatability failure and an intentionally exhausted linear-solve
budget. Correctly rejecting those last six cases is qualification success,
not a converged fit. All required cases stay in the result table.

A successful software result permits preparation of a separate finite native
optimizer qualification. It does not reopen calibration, supply an uncertainty
threshold or change any previous fit label. Earlier allowances stay closed.

**Completed:** [all 32 fits and eight direct controls pass](timing-stopping-qualification/INTERPRETATION.md).
All eight start-comparison groups agree. The run uses 1,008 analytical residual
evaluations and 905 bounded linear operations in 26 seconds. The
[native qualification plan](TIMING_OPTIMIZER_NATIVE_PLAN.md) defines the next gate.

[Next analyses](NEXT_STEPS.md) · [Technical roadmap](ANALYSIS_ROADMAP.md).
