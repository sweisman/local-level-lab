# Isolate curvature left after the shared source terms

Use the same twelve fixed generated points and six saved map epochs. Preserve
all 27 physical and 24 source columns. Do not fit coefficients or adjust points.

Let the forward calculation be f, the reference derivative J₀, and the saved
source map Cg. Define the remaining error by subtracting the reference linear
term and C[g(p)−g(0)]. Reanchoring g at the reference avoids assuming that a
floating evaluation is exactly zero there. Use the existing independent
source-map derivative implementation to obtain the error derivative at both
ends: f′−J₀−Cg′. Apply the endpoint average to this remaining error only.

Compare the existing shared-source expression and this diagnostic correction
with the saved native outputs. Report every point, both processing cases and
all six common epochs. Do not invent source maps for the other 287 epochs.
The known probe derivatives are diagnostic information, not unknown aircraft
calibration data. Sampled success cannot become an error bound.

Before execution, check an independent example with a cubic source term and
quadratic remaining error, a higher-order counterexample, and missing-column
failures. Verify reconstructed source/reference bindings and all input hashes.

Proposed finite maximum: two identities, two reference setups, fourteen
source-Jacobian oracles (two reference and twelve probe points), two reference
source-value oracles and twelve six-epoch comparisons. Zero native calls, LP
proposals, aircraft reads or observed fit starts. Use one numerical thread with
other allocations reserved and a 120-second cooperative ceiling. Freeze source,
inputs, environment and work accounting before launch; no retries, process
signals or allowance increases. Publish only from sealed results.
