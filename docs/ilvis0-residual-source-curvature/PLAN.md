# Saved curvature diagnostic after the shared source terms

Use the same twelve fixed generated probes and six saved map epochs. Preserve
27 physical and 24 source columns. Reconstruct the two original source-bound
references and require complete report agreement.

For a point p, subtract J₀p and C[g(p)−g(0)] from the saved native change.
Evaluate the independent source Jacobian at the reference and probe. Apply
the endpoint derivative average to this remaining error only: its derivative
is f′−J₀−Cg′. Do not fit coefficients, alter points, transfer old conditioned
radii or interpolate maps to unsaved epochs. Reanchor g explicitly; do not
assume a floating evaluation is exactly zero at the reference.

Verify an independent cubic-source/quadratic-error example, a nonzero source
center, a higher-order counterexample, and missing-column/report failures
before launch. Crosscheck the original shared-source residuals within the
fixed 1-micrometre numerical tolerance used by the preceding audit.

Finite maximum: two identities, two references, fourteen source-Jacobian
oracles, two reference source-value oracles and twelve six-epoch comparisons.
Zero native calls, LP proposals, aircraft reads or observed model-fit starts.
Freeze source, inputs, environment and work accounting. Use one numerical
thread with other allocations reserved; cooperative wall limit 120 seconds.
No retries, process signals or allowance increases. Publish sealed results only.

This is a diagnostic approximation, not a certified bound, uncertainty
coverage, an aircraft error law or evidence of a scientific model preference.
