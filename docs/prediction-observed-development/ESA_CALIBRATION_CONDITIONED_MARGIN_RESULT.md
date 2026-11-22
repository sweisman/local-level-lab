# The best forecast-conditioned margin remains unresolved

The broader test allowed up to 12.18 cm of uniform position error
when earlier position weights were free. This check restricts those
weights to the original forecast covariance. The previous direction,
with its earlier weights recomputed under that rule, certifies an
allowance of **0.86 µm** per coordinate for the saved affine forecasts.

The single numerical search reached its 2,000-iteration limit before
producing a usable witness or direction. The best allowable margin
therefore lies between **0.86 µm and 12.18 cm**. The upper bound comes
from the broader search. The result leaves open whether the original
conditioning can support a margin large enough for the integration
errors or the uncertainty in an aircraft forecast.

The single task completed with all six certificate calls accounted
for. Five software checks passed, including a comparison against a
known rational optimum. There were zero new aircraft fits and zero
reads of reserved observations.

[Frozen plan](ESA_CALIBRATION_CONDITIONED_MARGIN_PLAN.md) ·
[Verified evidence](esa-calibration-conditioned-margin-evidence/README.md)
