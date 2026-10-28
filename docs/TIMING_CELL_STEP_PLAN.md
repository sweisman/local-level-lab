# Qualify bounded steps within timing intervals

The [completed timing diagnostic](saved-timing-boundary/INTERPRETATION.md)
finds correct local derivatives but an unreliable compensating step across an
integration boundary. The next component should keep a proposed linear step
inside the interval whose derivatives describe it, while considering both
adjacent intervals and retaining every calibration coordinate.

## Software component first

Add a shared bounded linear-step component. Its inputs are a complete residual,
Jacobian, anchor point and physical box for each feasible timing interval.
Its output is a proposed step and predicted residual cost, not convergence,
uncertainty or a scientific decision. Charge each linear solve before execution;
use the existing `bvls` tolerance `1e-10` and 100-iteration ceiling.

Qualify smooth interior minima, internal-boundary minima, physical-bound minima,
coupled coordinates, redundant/zero columns, invalid boxes and exhausted charges.
Use independent closed-form minima or explicit low-dimensional face enumeration
as references. Preserve all 27 columns in the rank-deficient controls; agreement
in predicted observations does not require unique nuisance parameters.

Implement the shared algebra in `lll.timing_cells`, with a small
`lll.timing_cell_study` definition/evaluator and a saved-only
`lll.timing_cell_report`. Use one lifecycle task containing all 18 solves and an
append-only charge journal. The study has zero native-call allowance.

## Bounded saved-matrix review

After those checks pass, use all 18 feasible branch matrices already saved by
the four-point timing diagnostic: three distances on each feasible side. Do not
select only a favorable spacing. Each box retains the original physical bounds
and limits timing to its adjacent integration interval, clipped at the physical
offset limits. Verify the parent manifest, source-fit hashes and column order.

Allow exactly one solve per saved matrix: **18 charged linear solves**, one
thread, 100 iterations per solve and a ten-minute cooperative ceiling. Preserve
failed or interrupted solves; no retries. Generate no measurements, noise,
native calculations, forecasts or nonlinear fits. The prior diagnostic and
calibration allowances remain closed.

Compare proposals across sides and spacings, reporting predicted costs and
parameter-bound activity. These are linear predictions, not independently
evaluated physical costs. They cannot relabel the original failed fits.

## Next gate

Only after the component qualifies should a separate finite native diagnostic
evaluate its proposals. A complete boundary-aware optimizer still needs known
optima, repeatability and physical prediction checks before fresh calibration.
Keep the original cost, stationarity and position-change limits throughout.

[Next analyses](NEXT_STEPS.md) · [Roadmap](ANALYSIS_ROADMAP.md).
