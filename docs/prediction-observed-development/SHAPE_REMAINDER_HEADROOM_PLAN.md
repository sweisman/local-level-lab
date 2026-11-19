# How much nonlinear error could the shape separation tolerate?

Use the same archived zero-field pair, earlier fit-loss Jacobians, 27
calibration bounds, quadratic path terms and four working covariances as
the [conditioned calibration check](CONDITIONED_SHAPE_CALIBRATION_RESULT.md).
Keep its larger earlier squared-loss allowance of 0.01 and its original
local box. First drop the earlier loss constraint and compute the largest
affine closure allowed by the box alone.

Then assume, for the calculation, a uniform upper bound `delta` on the
Euclidean norm of the earlier standardized nonlinear remainder for each
model. If the exact earlier squared loss is at most `B` above the nominal
loss and the nominal standardized residual is `r`, the corresponding
linearized squared loss is at most
`(||r||² + B) + 2 delta sqrt(||r||² + B) + delta²`.
Use this expanded allowance in the existing convex support calculation.
Test `delta` values 0, 0.001, 0.01, 0.1 and 1. Reproduce the original
bound at zero. These are sensitivity values for an assumed bound.

Subtract the two support bounds from the nominal distance. This positive
margin, if any, is the total later nonlinear error that can be tolerated
along the fixed, conditioned and smooth-projected score direction before
the method loses guaranteed separation. The bound covers the two models'
errors together. No observed aircraft remainder bound follows from it.

Use one thread, four covariance operators, eight box support evaluations
and at most 40 affine support calls of up to 200 solver iterations each.
Read only the archived derivatives, earlier weighting inputs and released
forecasts. Start no native integrations or trajectory fits. Keep original
recordings, later receiver positions and reserved flight groups closed.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.shape_remainder_headroom freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.shape_remainder_headroom calculate
```
