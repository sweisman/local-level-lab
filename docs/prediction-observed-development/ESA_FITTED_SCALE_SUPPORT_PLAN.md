# Check error-scale support after aircraft calibration

Use the training part of the three sealed ESA 400/120 tangents
from the [conditioned calibration study](ESA_CONDITIONED_CALIBRATION_RESULT.md).
Restore the original covariance and verify the training derivatives
against the saved fit. Check how much of each proposed acceleration-error
pattern is consumed by calibrating the flight path. All three models
refer to the same training interval and are separate design checks.

Start the error patterns at the first training receiver report. Use
the existing 1°/s angular-motion trigger and 15-second response.
Express the acceleration loadings in the receiver's local north, east
and up directions at the first report. Whiten both the loadings and the
full mean design using the original covariance. Project out every
identifiable mean direction at relative rank tolerances 10⁻⁸ and 10⁻¹⁰.
Report the fraction of squared loading energy left for estimating each
error scale. Compare raw and retained Gaussian information with the
native error scale held fixed and the other acceleration term omitted,
using the 0.0001 and 0.001 m/s² reference standard deviations.

Three archived designs and six rank projections, one numerical thread,
zero new fits and zero native propagation calls. Use the 400 earlier
receiver reports and the earlier recorded angle increments from the
sealed design. Later receiver positions and reserved flights are outside
the input set. The projection assumes unrestricted local adjustments.
Active physical bounds, nonlinearity and forecast calibration remain
separate checks.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_fitted_scale_support freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_fitted_scale_support replay
```
