# Evaluate every saved interval-constrained proposal

## Question

Do the [18 saved linear proposals](saved-timing-cell-proposals/INTERPRETATION.md)
also remain stable when evaluated in the unchanged physical calculation?
Linear predictions alone cannot qualify the numerical method.

## Fixed inputs and procedure

Reuse the same four exposed generated-data points, all 18 proposals, every
feasible timing side and every spacing. Bind the completed timing diagnostic,
proposal manifest, source-fit hashes and full 27-coordinate vectors. Do not
choose only the proposal with the best predicted cost.

Reconstruct only those four existing streams, checking every saved input,
training position, error operator, residual and Jacobian. Use the original
compensated mean, noise propagation, gravity anchor, physical bounds and
numerical environment. No new seed families, nonlinear fits, forecasts,
aircraft records or protected observations.

At each point, repeat the baseline calculation twice, then evaluate every saved
proposal. Record actual cost, error of the linear prediction, full Jacobian and
the actual position change relative to the original saved point. Use the
existing training-residual unwhitener and common receiver-local coordinate
conversion for the position change. Report the original cost, stationarity and
position-change screens separately; none becomes a new convergence decision.

## Finite allowance and shared implementation

Four workers, one numerical thread each. At most eight complete residual/Jacobian
evaluations per point, 32 total; the complete sequence uses 26. Cooperative wall
ceiling: one hour. Expected runtime is roughly 5–15 minutes, dominated by exact
input reconstruction. Charge before work; no retries or allowance expansion.

Derive separate native reconstruction/call/packet ceilings from the existing
prefix formula with the eight-evaluation cap. Limit compilation to two kernels
per worker. Every earlier allowance stays closed.

Extract the shared saved-point execution plumbing rather than copying another
worker. Expose the training-only physical residual conversion through an
explicit optional capture callback, preserving the original default. Qualify
zero fitting/forecasting, complete proposal coverage, physical conversion,
source/environment guards and charging before creating the new freeze.

## Interpretation and next gate

Publish every actual/predicted comparison, including failed screens. Even a
successful result qualifies only these fixed-point proposals. A complete
interval-aware optimizer needs independent known-optimum and repeatability
qualification before another finite optimizer trial or calibration campaign.
The original failed labels and the 53-stretch findings remain unchanged.

[Next analyses](NEXT_STEPS.md) · [Roadmap](ANALYSIS_ROADMAP.md).
