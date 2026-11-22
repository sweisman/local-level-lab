# One calibration must explain both periods

This software check asks whether a shared calibration can explain both the
earlier receiver reports and the entire later path. It keeps the hardware
bounds and limits the calibration changes to those supported by the earlier
reports. One worked example rejects a model that fits the later path
perfectly if the earlier reports are ignored.

| Generated affine paths with correlated errors | Paths | One compatible calibration found |
|---|---:|---:|
| Correct mean, true calibration at a hardware bound | 128 | 123 |
| Deliberately shifted later mean, same nominal error law | 128 | 0 |

An independent dense calculation solved the single-parameter feasibility
problem directly and agreed in all 256 cases. Additional controls cover an
earlier period that already rules out the calibration bounds, directions that
the earlier data cannot measure, fixed calibration values, missing
approximation bounds and near-threshold roundoff.

## How the check works

The earlier reports define a confidence region within the calibration box.
The later criterion uses the whole residual vector after accounting for
correlation with earlier errors. A single point that satisfies both limits
establishes numerical compatibility. To rule out compatibility, the code
uses a lower bound on the achievable later residual across the whole earlier
region. The bound follows from convexity and holds in exact arithmetic
regardless of the optimizer's stopping flag. The software subtracts a
roundoff allowance and returns inconclusive when the finite search can
establish neither outcome.

With a fixed Gaussian covariance law, a shared scale bound and valid
approximation bounds for both periods, the probability of excluding a true
calibration is at most the sum of the three failure allowances. That sum was
5% in this control. The later approximation bound must include the part of
any earlier approximation error carried forward by the conditioning. The
result describes compatibility with the fitted observations. Prediction
accuracy and absolute physical adequacy still require separate checks.

The structured implementation carries per-coordinate approximation bounds
through the same whitening calculation as the residuals. An error confined
to the earlier period can affect the later score through this calculation.
The new implementation enclosed every signed corner of a small correlated
control, including that earlier-to-later effect, without a dense trajectory
matrix.

The aircraft calculation still needs supported bounds on the gap between
each local linear approximation and the nonlinear trajectory throughout the
earlier calibration region. The [saved native replay](GENERATED_JOINT_PROFILE_SAVED_RESULT.md)
and [local replay](GENERATED_LOCAL_PROFILE_RESULT.md) found errors large
enough to matter. This software check leaves the aircraft decisions and
reserved flight groups untouched.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m pytest -qs \
  analysis/tests/test_bounded_joint_path.py
```
