# What the fresh-noise pilot established

**All 48 fits converged and passed the unchanged position-error checks.**
The calculation finished in 43.8 minutes. A separate 17-check audit verified
the saved results and reproduced the previous study's report unchanged.
No fits were repeated during reporting.

These are generated two-minute records, not new aircraft findings. Each model
fits data generated under that same model. The experiment tests prediction
software with known measurement errors; it does not choose an Earth model.

## What improved

The earlier study used one noise seed and retained four numerical failures.
This pilot used two new, preassigned seeds, with calibration estimated anew.
All starts passed under the original bounds and evaluation limits. All raw
and error-conditioned forecasts met the same 10 m horizontal / 30 m height
RMS screens. Earlier failures remain unchanged.

Select one start per setting by earlier-data fit cost, before inspecting later
errors. The resulting 24 primary forecasts have horizontal RMS errors of
2.49–3.78 m. Starts and settings sharing a seed are dependent; these are two
independent noise realizations, not 48 independent experiments.

## What remains unresolved

Every selected fit reaches at least one calibration limit. The reported
noise scale assumes that fitted calibration is known exactly. Dividing the
largest later coordinate error by that scale gives scores of **7.50–11.22**.
Those scores show that this incomplete uncertainty calculation cannot be read
as calibrated confidence. They do not change the physical accuracy result.

The next step is to include uncertainty in the bounded calibration parameters
and preserve directions the training observations cannot identify. Two pilot
seeds cannot determine a tail threshold or establish predictive coverage.
New aircraft fits and reserved ESA confirmation groups remain gated.

[Every start and its scores](results.csv) · [Verified report](README.md) ·
[Frozen plan](PLAN.md) · [Next analyses](../NEXT_STEPS.md).
