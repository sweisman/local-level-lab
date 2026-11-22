# Use the earlier GPS directions that matter for the forecast score

The [first earlier-loss proof](ESA_CONTRAST_TRAINING_SUPPORT_RESULT.md)
rules out the two calibration values behind the broader upper bound.
Its two support inequalities barely improve the bounds on changes
that reduce the forecast contrast. The lower allowance stays at 2.25 cm.

Keep the compact contrast and the original earlier-loss criterion.
For each candidate, scale the earlier position Jacobian by the original
calibration widths and decompose it by singular value. Construct
earlier residual directions whose calibration effects approximate the
forecast score coefficients. Use three relative singular-value cutoffs
of 10⁻⁴, 10⁻⁷ and 10⁻¹⁰. Evaluate both signs without selecting a cutoff
from any later observation. Treat the directions only as numerical
proposals. Verify their bounds directly through the archived whitening
operator and retain every omitted calibration coordinate in the original
box support. Check both previously frozen earlier-error settings, 0
and 0.1 in the whitened norm.

Report the strongest verified lower allowance beside the existing
2.25 cm bound and 4.03 cm reference. If the single batch fails to reach
the reference, preserve that outcome and move priority to the receiver
and aircraft uncertainty checks before further tuning this contrast.
No result qualifies an aircraft uncertainty rule. No later GPS
positions or reserved flights enter the calculation.

Freeze one task and one numerical thread. Charge one input check, one
decomposition per candidate, and 24 support checks, for 27 calls and
27 steps. Keep the 180-second cooperative allowance and one separately
charged technical recovery attempt. Save every cutoff and score sign,
including any direction with no support improvement.
