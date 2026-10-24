# Two-minute noisy training and prediction

The short native protocol checks data handling and error conditioning, but two
seconds and six earlier positions do not identify calibration. This separate
study tests the estimator on two minutes of generated motion, with more earlier
observations and the existing full fitting allowance.

## Frozen comparison

Use 24 starts: three generating physical candidates, two processing assumptions,
two input-error laws and two declared initial points. Use one fixed receiver
policy, `reported-short-v1`. Each case contains 36,000 IMU intervals at 300 Hz,
119 query times from 0.5 seconds at one-second spacing, 79 earlier receiver
positions and 40 later truth positions. Retain all 26/27 calibration columns.

The motion and observations come from the existing independent generated-flight
implementation, including climb and changing course. The original constant
calibration bounds, midpoint covariance anchor, noise settings, numerical stopping
rules and 10 m horizontal / 30 m height RMS accuracy screen remain unchanged.
Preserve the maximum-error checks too. Fit each candidate to its own generating
truth; this is not an Earth-model selection campaign.

Keep increment noise and endpoint-shared rate-point noise separate. Use the
explicit versioned stress settings and named seed streams. Both starts share
the same measured inputs within a generating model, processing case and input
law. Never pass true initial state or calibration to the fitter.

Save raw and earlier-error-conditioned forecasts before opening later physical
truth. The physical-position target omits future receiver-error contributions.
Future receiver transformations use the last earlier value only. Preserve the
exact training covariance prefix and the fitted-point/model/error binding.

Report numerical convergence, raw physical accuracy, conditional physical
accuracy, calibration rank and active-bound abstention separately. A successful
point prediction does not establish calibrated coverage. Do not suppress
failures or count short conditional intervals as calibrated uncertainty.

## Execution and audit

Use the shared `lll.studies` lifecycle and shared evaluator/report components.
Before launch qualify that production evaluator and saved-only auditor on the
finite short matrix, including corrupted target/count/normalization rejection.
The auditor must recompute scores from saved predictions and truth without
refitting, rerunning native propagation or regenerating truth.

Freeze sources, environment, recipe, exact task limits and qualification evidence.
Allow 24 starts, at most 200 evaluations plus one raw forecast per start, four
single-thread workers and a cooperative two-hour ceiling. Covariance construction
is also native work and is charged separately in the same task allowance.
Prepay each finite block; preserve attempted-work snapshots and unused charges.
No retries, transfers or extension of a completed allowance are permitted.

The definition computes conservative native-call and packet-query limits from
the fixed prefix, cadence and evaluation ceiling. Construction has separately
charged sample and normal-variate limits. Permit at most two native builds per
worker, reusing its verified cache across sequential tasks.

No original aircraft inputs, observed fits or protected confirmation recordings
enter this study. The completed twenty-minute noise failure is preserved; this
study cannot relabel it. Only verified results can determine the next gate.

[Nonlinear plan](../integrated-noise-covariance/NONLINEAR_PLAN.md) ·
[Short native protocol](../integrated-noise-covariance/short-native-protocol-qualification/README.md) ·
[Prediction protocol](../PREDICTION_VALIDATION.md).
