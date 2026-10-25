# Test uncertainty after calibration is fitted

The known-calibration experiments separate noise growth from fitting. They do
not answer the practical question: does a prediction-error allowance still
describe the errors when the software must estimate the calibration itself?

Start with the existing, verified two-minute generated study. Its 24 fits already
retain the earlier observations, later predictions, later truth, fixed-parameter
conditional covariance and numerical outcomes. Use those saved files; do not
repeat a fit or generate another trajectory for this first step.

## Saved-data scoring gate

Add a shared `lll.prediction_scores` component and a small
`lll.fitted_prediction_scores` saved-results adapter. Use the existing
`lll.studies` lifecycle, closed-study access and primary-selection helper.

For each fit, take the later coordinate error divided by its corresponding
conditional standard deviation, and retain the largest absolute value across
the complete later block and all three axes. Use latitude/longitude radians and
height metres consistently with the stored covariance; wrap longitude residuals
at the chart boundary. This avoids mixing a physical metre error with an angular
covariance. Report physical errors alongside this dimensionless score.

This score is a diagnostic, not a confidence level. The supplied covariance
still treats fitted calibration as known. Comparing it with errors from the
complete fitting procedure shows what that omission costs; it does not cure it.

Preserve all 24 starts and their four numerical failures. Select each reported
primary by qualified training cost, then declared start order, using the existing
helper. Never select a start by its later score or physical accuracy. Retain a
group without a qualified start as unavailable. Do not count the shared noise
seed as 24 independent replications or estimate a calibration quantile from it.

The first freeze permits only the declared completed parent study: 24 saved
fits, at most 40 later epochs per fit, and three coordinates. Native calls,
optimizer starts, noise draws and original/protected reads are zero. Use one
numerical thread and a five-minute cooperative ceiling. Qualify scoring and
binding checks before preparing that saved-data run.

Tests cover units, complete-block maxima, longitude wrapping, invalid/zero
standard deviations, incomplete curves, training-only primary selection, failed
fit preservation and the shared-seed warning. Recompute the parent's scores and
verify its manifest, fitted-point and covariance bindings before using them.

## Qualification with new noise realizations

After the saved-data gate, prepare a separate finite full-pipeline qualification.
It must estimate calibration from earlier observations for every draw, retain
all candidate/processing cases and starts, and preserve numerical abstentions.
It must not supply true calibration or later positions to fitting, weights,
initialization or primary selection.

Independent calibration and validation draws will be needed before a prediction
score can set an uncertainty threshold. Freeze their identities, nuisance
scenarios, fitting budgets and coverage objective first. Any resulting coverage
statement is limited to the declared simulation domain. It does not establish
actual archive noise or calibrate the two-stage Earth-model decision automatically.

Keep the 10 m horizontal / 30 m height descriptive screen and all failed studies
unchanged. No new aircraft fits or reserved ESA data are released by this plan.

[Noise diagnosis](../noise-nonlinearity/remainder-diagnosis/README.md) ·
[Prediction protocol](../PREDICTION_VALIDATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
