# Saved shared-source map audit

Use all twelve sealed nonlinear probes from the completed generated-data
diagnostic. Compare six saved epochs per point: 2, 10, 30, 180, 290 and 438
seconds. Keep the two processing cases separate.

Rebuild one source-bound reference per case and require exact agreement with
the original saved reference. Verify that the old six native centers and all
physical Jacobians match the corresponding newer batch outputs. Reuse only
coefficient maps with the same source, reference and shared normalization.

For each fixed point, evaluate its 24 shared source coordinates once. Compare
the saved native position changes with the 27-column linear expression and
the full 51-column expression. Report residuals and the three shared-block
contributions. Do not optimize or adjust the points. Do not transfer old
training-conditioned radii: these probes need not satisfy that training region.

Finite scope: two identities, two reference setups, twelve source-coordinate
oracles and twelve map comparisons covering 72 saved epochs / 216 coordinate
residuals. Zero native integration, LP proposals, aircraft reads or model fits.
Use one numerical thread with other allocations reserved; cooperative wall
limit 120 seconds. No retries, process signals or allowance increases.
Freeze the sources, saved inputs, environment and hash references before launch.
Publish only from sealed results.

This is discrepancy attribution, not prediction coverage, a check of unobserved
calibrations, an aircraft error model or scientific significance.
