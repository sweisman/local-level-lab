# Saved-tangent audit of the last matched-trial target

Both the primary and repeat stopped before their evaluation caps. Their saved endpoints pass stationarity but fail fresh objective and axis-RMS position checks. This audit uses their preserved residuals and Jacobians only: **zero native predictions and zero archival fit starts**. An affine correction is a local numerical diagnostic; it cannot resolve the flight comparison.

The zero correction is feasible and leaves the objective unchanged. A successful local solver must therefore be checked against that baseline. Column scaling changes numerical coordinates, with bounds transformed consistently; it does not change the affine problem.

| Endpoint | Local solve | Success | Feasible | Signed affine objective change | Step norm |
|---|---|---|---|---:|---:|
| primary | original_bvls | True | True | -0.00112023656 | 0.0277051 |
| primary | column_scaled_bvls | True | True | -0.00112023656 | 0.0277051 |
| repeat | original_bvls | True | True | -0.000885176951 | 0.0240835 |
| repeat | column_scaled_bvls | True | True | -0.000885176951 | 0.0240835 |

Full singular spectra, diagnostic ranks, column norms and correction vectors are retained in the [audit data](diagnosis.json). Reported ranks are descriptive; no scientific rank cutoff changes. Predicted affine improvement needs a separately bounded full-model check before it can inform a revised stopping or step policy. The original unresolved labels and all earlier failures remain unchanged.
