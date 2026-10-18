# Diagnosis of the generated height-only endpoint

## Fixed question

Diagnose the single failed endpoint from the completed projected-fitting
qualification. Reconstruct its independently generated twelve-second motion,
with the same model, clock, bounds, initialization, covariance, six parameters
and extended native arithmetic. Preserve the qualification and its unrun tests.

This is a fixed-endpoint diagnostic, not continuation of optimization. No
original recording is read and no optimizer is started. Linear bounded solves
are diagnostic proposals only; their outcomes cannot relabel a failed fit.

## Fixed operations

Use exactly **33 generated-motion tangent evaluations**:

1. Reproduce the saved endpoint and its cost/stationarity: one evaluation.
2. Repeat that identical point to check determinism: one evaluation.
3. Evaluate the independently known generating parameters: one evaluation.
4. Check every derivative with central differences at normalized steps 0.001
   and 0.0001: six parameters × two signs × two step sizes = 24 evaluations.
   All points must remain feasible; reject an unsupported point rather than
   changing its step or silently clipping it.
5. Calculate two bounded linear corrections at the original endpoint: the
   existing unscaled BVLS correction and a column-scaled formulation of the
   same feasible linear problem. Evaluate fractions 1, 1/4 and 1/16 of each
   correction, always starting from the original endpoint: six evaluations.

Retain all columns, including weak or zero columns. Do not truncate singular
directions or reinterpret full numerical rank as unique calibration. Report
singular vectors, column norms, linear versus nonlinear changes, physical
retained/full-coordinate errors, and componentwise stationarity. Scaling must
transform the step bounds consistently; both formulations use the same original
linear residual and feasible physical parameter region.

## Persistence and limits

- Exactly one diagnostic identity; **33 native calls maximum** and **zero fit
  starts**, with no retries or expansion.
- **Four total numerical threads**, **120 seconds** maximum after compilation.
- Freeze this plan, parent completion/manifest/summary, numerical environment,
  exact sources and endpoint before launch. Verify parent source hashes.
- Charge each uniquely named call before execution in a durable journal; save
  its full and projected residual/Jacobian with hashes. Use an exclusive lock.
- A failure stops the diagnostic and remains recorded. Charged/completed work
  cannot restart. Publication uses saved arrays and performs no integration.

Constructed-matrix tests first check the scaling/bounds mapping, retained weak
columns and derivative-error summaries. These cheap software tests are separate
from the 33-call native allowance. An informative correction is a diagnostic
result, not qualification of a new solver or authorization for recorded refits.
