# Can calibration changes close the shape gap after conditioning?

Use the two archived zero-field forecasts and their 27-column derivatives
from the [calibration contrast study](ESA_CALIBRATION_CONTRAST_RESULT.md).
Both were selected by earlier fit cost in the profiled-removal increment
setting on ESA recording 187. Reuse that study's original calibration box,
0.10 normalized local radius and earlier squared-loss allowances of 0.001
and 0.01. These are fixed development sensitivities.

Use the conditional means and four covariance choices in the original
[forecast pair study](FORECAST_PAIR_INFORMATION_RESULT.md). Transform the
forecast differences and the nine smooth error terms into the common
conditional score. Use the unit direction between the two forecasts after
projecting out those terms. Verify its length against the saved comparison.

Whiten each full derivative history, including its earlier part, before
retaining the later rows. This carries the calibration change through both
the prediction and its conditioning on training data. Bound each model's
shift toward the other in the fixed direction. Use the original earlier-fit
Jacobian and residual for the permissible loss, with the shared convex
support solver. Subtract the two certified upper bounds from the nominal
distance and keep zero as the lower limit.

The bound applies to the local affine derivatives. It does not certify the
nonlinear calibration region, any aircraft covariance or statistical power.
Allow four covariance operators and 16 small support calculations, each
using the solver's existing 200-iteration limit. Use one thread. Read only
the saved derivatives, earlier covariance inputs and forecast receipts.
Open no later GPS positions or protected data and start no trajectory fits.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.conditioned_shape_calibration freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.conditioned_shape_calibration calculate
```
