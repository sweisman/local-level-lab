# Joint future-path compatibility software control

The current generated three-candidate comparison uses conservative
coordinate-by-coordinate whole-path ranges. All candidate ranges overlap.
A joint path can still contain information because one fixed calibration
change must explain **every** later coordinate. This plan qualifies only the
linear algebra for that observation, before connecting it to a model test.

Given a finite, already whitened later residual vector `r`, a full
later-path Jacobian `D` with every declared calibration column, and
predeclared bounds `lower <= delta <= upper`, compute
`min_delta ||r - D delta||²` with a bounded least-squares solver. Keep rank
diagnostics using an explicit singular-value tolerance. Report original
and profiled squared residual, fitted correction, boundary coordinates,
solver status and exact dimensions. Validate known interior and boundary
solutions, rank-deficient columns, nuisance-absorbed contrasts and axis/
column permutations. Fail closed on nonfinite or incomplete input.

The future observations choose `delta` in this calculation. Consequently
the number is a **model compatibility/profile diagnostic**, not an
earlier-only prediction error. No chi-square reference distribution,
significance threshold or model winner follows from the software control.
Any future aircraft use must freeze the same whole-path whitening and
calibration policy across candidates, include nonlinear remainder and
boundary checks, and calibrate the complete two-stage selection with
separate generated and independent observed evidence. Do not use a fitted
model's own future residuals to tune the threshold.

This stage uses synthetic vectors only: zero aircraft reads, zero native
integrations, zero new fits, and one numerical thread. The old range
comparisons and frozen outcomes remain unchanged.
