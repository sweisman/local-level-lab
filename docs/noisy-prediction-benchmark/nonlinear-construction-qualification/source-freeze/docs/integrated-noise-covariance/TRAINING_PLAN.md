# Connect the error model to training-only native fitting

The input-specific native propagation and receiver combination pass their
182-check qualification. Linear calibration uncertainty is also checked.
The next gate connects those components to the existing fitting interface,
before any new aircraft fits or expensive noisy fitting study.

## One fixed weighting per declared training anchor

Initialize using earlier receiver observations and inertial inputs only.
Construct the declared error operator at a fixed, recorded calibration anchor
chosen without generating truth, preferred-model labels or later receiver
positions. Keep that operator fixed throughout each optimization. Changing
weights while ignoring their derivatives would define a different objective.

Use the correct source law: incremental noise for recorded increments, shared
sample noise for the declared ESA rate-point conversion. Preserve all axes,
receiver correlations and the full calibration domain. Freeze receiver-frame
conversions and any later covariance extrapolation using earlier information
only. No future receiver values or quality fields may choose training weights.

Use the shared model and solver interfaces, without copying a worker or patching
process globals. Add an explicitly supplied structured observation-error path;
the existing dense path must retain its meaning. Do not allocate a dense
epoch-by-epoch covariance merely to construct a native problem. Whiten residuals
and every active derivative column with the same operator. Preserve extended
precision subtraction, longitude handling and the original stopping checks.

Different physical candidates may imply different propagated covariance.
Preserve its log determinant and full Gaussian normalization. Weighted residual
sum of squares alone must not become a cross-candidate likelihood comparison.
Within one frozen weighting, the constant determinant does not change the
optimizer's solution. No new decision thresholds are introduced.

## Predictions and calibration limits

Store the unadjusted trajectory separately from a prediction conditioned on
earlier errors. Resolve residual signs explicitly: model-minus-receiver fitting
residuals and receiver-minus-model prediction errors have opposite signs.
Never correct a forecast using receiver measurements from the withheld period.

Keep every nuisance column in calibration uncertainty and rank checks.
The linear uncertainty component assumes unrestricted parameters. Do not apply
it as a coverage claim when the fitted solution is at a bound or when nonlinear
behavior is unqualified. Preserve those cases as unsupported, with their point
forecasts and numerical outcomes available for diagnosis.

## Software gate and finite allowance

Qualify at most 32 deterministic native adapter cases and 32 interface checks,
600 packets, twelve queries and all 27 calibration columns. The native matrix
contains 24 cases: three models, two processing assumptions, two gravity rules
and two input-noise laws. Each uses 160 packets, ten earlier queries and two
later queries. Compare residuals and derivatives with
independent dense whitening at the same frozen covariance. Include both source
laws, model/processing/gravity combinations, training-prefix invariance when
later material changes, determinant normalization, bounds/rank abstention,
invalid-frame rejection and unchanged legacy behavior. This gate checks
adapter algebra; it does not substitute for independent noisy physical controls.

Allow at most 12,000 native calls, 1,000,000 conservative packet steps,
8,000,000 packet-query visits, two cached builds, one numerical thread and a
cooperative five-minute ceiling. Precharge whole-case work before execution.
No random draws, optimizer starts, original reads or protected reads occur.
Freeze exact sources, environment, inputs and case charges before qualification.

Each native case prepays at most 450 native calls, 15,000 conservative packet
steps and 300,000 packet-query visits. Two builds are prepaid separately.
Finite differences retain every active column and use normalized steps of
0.01 for gyro offsets, 0.001 for the removal fraction and 0.0001 elsewhere.
The derivative relative discrepancy must not exceed 0.0002; small-column
absolute allowance is 0.0000001 in whitened units. Dense whitening agreement
uses relative tolerance 0.000000001 and absolute tolerance 0.00000001.
These are adapter arithmetic checks, not measurement accuracy limits.

Only after this gate passes should a separate finite noisy end-to-end fitting
study be frozen. That study must test training-estimated calibration, active
bounds, prediction accuracy and nonlinear uncertainty coverage under the same
declared assumptions. Preserve the completed failed noise study, its 10 m/30 m
accuracy limits and all earlier allowances. Broader observed fitting and the
reserved confirmation groups remain gated.

[Native qualification](../native-noise-linearization/README.md) ·
[Linear calibration](CALIBRATION_PLAN.md) · [Receiver assumptions](../ESA_ERROR_POLICY.md) ·
[Prediction protocol](../PREDICTION_VALIDATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
