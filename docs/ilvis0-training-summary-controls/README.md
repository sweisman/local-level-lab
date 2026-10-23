# Connecting training summaries to saved native predictions

This check applies the signed-summary interface to six sealed generated sources, covering all three candidates and both processing assumptions. It reuses the original five training epochs, native predictions, Jacobians and nonlinear bound reports. No integration or fit is repeated.

| Candidate | Processing | Coordinate inequalities reproduced | Signed-summary inequalities audited | Result |
|---|---|---:|---:|---|
| Globe + field | Zero removal | 30 | 24 | Passed |
| Globe + field | Profiled removal | 30 | 24 | Passed |
| Globe, zero field | Zero removal | 30 | 24 | Passed |
| Globe, zero field | Profiled removal | 30 | 24 | Passed |
| Stationary disc | Zero removal | 30 | 24 | Passed |
| Stationary disc | Profiled removal | 30 | 24 | Passed |

Unit rows reproduce every original coordinate inequality. Twelve signed time-polynomial summaries are checked again with exact rational arithmetic. All 27 physical parameters and 51 source-expression columns remain present. Unknown remainder signs are not canceled; rounded projected coefficients have a separate allowance over the full box.

This uses the original deterministic one-metre error premise and its conservative signed sum. It does not apply the dense-cadence Gaussian noise examples to these sparse observations, add observations, tighten calibration bounds or recalculate later positions.

**The full prediction method remains unqualified.** The next scientific test needs complete training cadence, matched nonlinear source bounds and the declared error family, followed by whole-period prediction coverage. The 53-stretch findings remain unchanged.

[Frozen scope](PLAN.md) · [Next step](../ilvis0-joint-projection-controls/NEXT_PLAN.md) · [Error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md)
