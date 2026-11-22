# Test whether earlier GPS limits tighten the same shape contrast

The [2.25 cm result](ESA_COMPACT_FORECAST_MARGIN_RESULT.md) lets every
calibration value vary within its original box. The [full replay](ESA_CONTRAST_REPLAY_RESULT.md)
finds small integration errors at the two checked points that pass
the earlier-loss limit. The calibration pair behind the 2.25 cm upper
bound has not been checked against the earlier GPS reports.

Use the saved 51-column design and original earlier loss for each
candidate. First, check the saved affine upper-bound calibration pair
under the earlier-loss rule. Use the residual direction at this pair
to form a necessary earlier-data inequality for each candidate.
Recompute its coefficients through the archived whitening operator
with outward rounding. Combine each inequality with the unchanged
calibration box and the same compact forecast contrast. Check both
signs and report any increase in the certified lower allowance.

Repeat the proof with zero and 0.1 units of unshared earlier error in
the whitened norm. These are the earlier comparisons' sensitivity
settings. A failed witness no longer supplies an upper bound for this
restricted problem. A weak inequality leaves the existing lower bound
in place. No new optimization of the forecast direction is authorized
by this plan.

Freeze the original compact result, covariance factors, calibration
columns, and finite software controls. Use one task, one numerical
thread, no native passes, and five bound calls with five charged
steps. Use a 180-second cooperative time limit and one separately
charged interrupted-task recovery. No new aircraft fits, receiver
reads or reserved flights are used.
