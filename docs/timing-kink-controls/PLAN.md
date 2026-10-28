# Known-answer tests for an internal timing boundary

The [saved corrections](prediction-linear-timing-review/README.md) cross a
timing boundary in both failed fits and in neither successful control. Before
new native calculations, test whether the existing numerical check can reject
a mathematically exact minimum when the slope changes at a boundary.

## Small software qualification

Use four analytical one-parameter cases on the fixed interval −1 ≤ u ≤ 1:

1. A smooth minimum with residuals `[15, b(u−c)]`, at `c = 0`.
2. A boundary-shaped minimum with residual `15 + b|u−c|`, at `c = 0`.
3. The same minimum translated to `c = 0.25`.
4. A smooth residual `15 + bu`, evaluated at zero although its minimum is at −1.

Use `b = 0.00005`. The minima follow directly from the formulas, independently
of any optimizer. Supply the correct right-hand derivative at each kink and
verify both one-sided derivatives separately. Call the original, unchanged
stability checker once per case, with an analytical evaluator and its existing
cost, stationarity and position-change limits.

These are ordinary deterministic software checks: at most four bounded linear
solves and four fresh analytical evaluations, one thread, no native calls,
aircraft observations, noise draws or nonlinear fits. Preserve rejection as an
expected outcome where the original check cannot certify a known minimum.

## Interpretation

An exact counterexample would identify a limitation of the smooth numerical
check. It would not prove that the saved aircraft-simulation failures have the
same cause, justify accepting them, or qualify a replacement solver.
Native two-sided derivative tests still require their own reviewed finite plan.

[Next analyses](NEXT_STEPS.md) · [Roadmap](ANALYSIS_ROADMAP.md).
