# Scalar calibration projection controls

## Question

How much of a constructed acceleration-magnitude difference lies outside the
local seven-parameter calibration tangent, and does the suggested linear
correction actually reproduce that improvement nonlinearly within the bounds?

This is a software diagnostic, not an observed fit or nonlinear identifiability
test. Neither a small nor a large projected residual establishes scientific
model discrimination.

## Fixed matrix and allowances

Use the independent Cartesian reference's stationary, eastbound,
changing-direction and climbing profiles, three truth models, all three
comparison candidates, and both reference body-orientation histories. Use 121
epochs from 0 to 600 seconds at five-second spacing. These are constructed
controls, not selected aircraft trajectories or an assumed flight population.

The matrix has **72 identities**, each with 121 independent-reference evaluations,
121 candidate-force evaluations and one local calibration analysis: at most
8,712 reference evaluations, 8,712 candidate-force evaluations and 72 SVDs.
No optimizer starts, native integrations, original-file reads or retries.
One worker, four total numerical threads, 60-second wall-time ceiling.

Apply the same calibration bounds to every candidate: three gains ±0.15,
three acceleration offsets ±0.25 m/s², gravity adjustment ±0.05 m/s². These
are existing assumed search bounds, not measured sensor errors. Keep all seven
columns and the complete singular spectrum. Use relative rank tolerance 10⁻¹⁰.

## Checks fixed before execution

- For same-model cases, exact scalar agreement must be within 10⁻⁹ m/s².
- Projection cannot increase the residual norm beyond 10⁻¹² m/s² rounding.
- The normalized calibration tangent must be orthogonal to the retained residual
  within 10⁻⁹ times max(1, tangent norm × residual norm).
- Preserve all wrong-model outcomes, ranks, linear corrections and nonlinear
  checks. No minimum separation or pass threshold is imposed on wrong models.
- Report nonlinear residuals only for suggested corrections inside all bounds.
  An unbounded local projection is not a feasible nonlinear fit, and a feasible
  linear step is not an optimized nonlinear solution.

Freeze task identities, sources, environment and limits before launch. Charge
each identity before evaluation and preserve failures. Completed work cannot
restart or transfer unused allowance. Publication verifies saved hashes and
performs no numerical analysis.

The earlier frozen studies, main 53-stretch results and unresolved horizontal-only
sensitivity result are unchanged. Recorded-data use remains downstream of
nonlinear calibration ambiguity, timing, quantization and uncertainty controls.
