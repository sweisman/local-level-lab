# Translate the shape-direction error limit into metres

Use the same sealed zero-field pair and four working covariances as the
[nonlinear headroom calculation](SHAPE_REMAINDER_HEADROOM_RESULT.md).
Reproduce the distance and the unit shape direction after conditioning
and removing the nine smooth position terms.

For the fixed innovations operation `W` and a later shape direction `q`,
compute the physical-coordinate coefficient vector `Wᵀ q`. Set the earlier
entries of `q` to zero and run the adjoint backward through the full
520-report period. Earlier position errors can still affect the later
score through the conditioning. Use outward-rounded intervals with 384
decimal digits for the adjoint of the stored numerical coefficients. Verify the result against
the forward operator on a fixed calculation.

For each covariance, report the upper sum of absolute coefficient sizes
before and after the cut. Divide the [conditional headroom](SHAPE_REMAINDER_HEADROOM_RESULT.md)
of 12.78 by twice the full-period coefficient sum. This is a sufficient
componentwise error limit in metres for each of the two candidates, under
the assumed earlier remainder norm of at most 0.1. Report the separate
limits if one period has zero error. A later full-region proof may instead
supply different bounds by axis and time.

The calculation qualifies a transformation of an error bound. It establishes
neither a physical remainder for the archived integrator nor a covariance
law for an aircraft. Use one thread and four finite adjoint passes, with
no fits, integrations or original or reserved recording reads.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.shape_remainder_metres freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.shape_remainder_metres calculate
```
