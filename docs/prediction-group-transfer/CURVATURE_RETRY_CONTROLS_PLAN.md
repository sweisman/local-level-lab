# Test a curvature-guided shorter solver step

Four [saved zero-removal fits](../prediction-observed-development/ESA_400_120_MODEL_MATRIX_STOPPING.md)
rejected the full correction near a stable training cost. Their fresh
position checks still failed. A cost-subtraction audit did not account for
the rejected full correction.

Add a candidate retry for an evaluated, rejected full step. For residual
`r`, linear change `p` and measured full-step residual `r1`, use
`r + a*p + a²*(r1-r-p)` to select one fraction strictly between zero and
one. Test that fraction against the real residual, using the existing
minimum agreement ratio against the linear prediction. The retry can occur
once for a given unchanged full proposal. All live calls count against the
same evaluation limit. Keep the original fallback and the complete fresh
position check. The current solver remains the default.

Use four new generated problems with known solutions and two fixed starts
for each. The problems cover a curved interior, both active-bound signs
and a weak direction with a large constant residual. Compare the current
trust solver and the optional retry, for 16 tasks with up to 40 residual
evaluations each. Keep all costs, calls, failed trials and dispositions.
A numerical pass requires the unchanged stopping gate, objective within
1e-7 of the known value and parameters within 1e-4. Only report a
qualification if the retry meets all eight cases and succeeds in accepting
a fractional step on at least one. A pass qualifies these controls and
permits a separate flight-scale generated check. It does not qualify
another aircraft fit.

Use one worker and one thread for up to 60 seconds. Technical
interruptions use the separately qualified recovery allowance. Use no
aircraft measurements, forecasts, native calls or reserved flight groups.
