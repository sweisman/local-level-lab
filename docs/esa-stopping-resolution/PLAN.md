# Fixed-point stopping-resolution diagnostic

## Question and boundary

The [completed height-gravity comparison](../esa-observed-height-pilot/README.md)
returns all 24 forecasts. Eight fits pass numerical checks. Seven specified-field
globe fits pass the saved stationarity and position checks but fail the separate
relative cost-change check. All eight specified-field forecasts meet the fixed
training and later accuracy limits; only qualified fits enter model comparisons.

Does the saved cost-stability failure reproduce at the exact fitted parameters,
and how do actual and linearized cost changes behave as the existing bounded
correction is scaled? This diagnoses the calculation. It changes no stopping
threshold, fitted point, convergence label or scientific decision.

## Fixed inputs and calculations

Require the closed, hash-verified height-gravity report and its frozen numerical
sources/environment. Reuse all 24 saved fitted points, including failed fits;
do not select points by their forecast errors. Preserve every nuisance column.

Use only the original prepared increments up to the declared training support,
the earlier 800 receiver positions, their working covariance and the earlier-only
gravity anchor. No later receiver position, original aircraft file or protected
confirmation observation is an input. Perform no fitting and no full forecast.

For each point:

1. Calculate two fresh residuals and all derivative columns at the same point.
   Preserve exact-repeat flags and differences from the saved training cost.
2. Call the unchanged shared fresh-position check to obtain its bounded local
   correction and its fresh evaluation. Preserve its original pass/fail result.
3. Evaluate that correction at fractions 1/2, 1/4, 1/8, −1/8, −1/4, −1/2 and −1,
   clipping only to the existing feasible parameter box. Record requested and
   actual parameter changes, including clipped or duplicate points.

Together these require at most ten native sweeps per identity. If the shared
check cannot form a correction, preserve its reason and stop that identity;
do not invent another direction or reuse its unused allowance.

Save fresh costs, residual and derivative bindings, actual physical position
changes, linear predictions and every original label. Distinguish deterministic
repeats, local nonlinearity, timing boundaries and possible arithmetic effects.
This probe alone does not prove a roundoff bound, a global optimum or a cause.

## Finite allowance and qualification

Freeze a separate definition before execution: 24 identities, at most **240 native
calls**, **46,054,464,000 packet/query work units**, four workers with one numerical
thread each, and a cooperative **one-hour** ceiling. There are zero nonlinear
optimizer starts, original/protected reads and retries. The local bounded linear
correction is the existing stopping check, not a new calibration fit.
Charge every native sweep before
execution. No unused allowance from the observed comparison is available.

Before preparation, software checks must cover exact fixed-point reuse, earlier-only
inputs, all models and processing cases, every derivative column, feasible clipped
probes, unavailable-correction handling, native accounting and unchanged labels.
Freeze the passing test report together with source and environment hashes.

Report every identity. A completed diagnostic does not make an unresolved fit
qualified. Any corrective numerical method needs its own known-answer qualification
and finite freeze before a new observed comparison. Accuracy limits, calibration
bounds and the seven protected confirmation groups remain unchanged.

[Stopping checks](../NUMERICAL_STOPPING.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
