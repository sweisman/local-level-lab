# One error budget for training and prediction

The staged method needs an error allowance for each position observation.
This new component converts supplied Gaussian noise bounds into those metre
allowances, covering the complete declared set of training and future epochs.
It does not treat samples as independent or count each coordinate as a separate
successful test.

**15 focused checks pass.** All six small end-to-end model/processing cases pass:
combined receiver/IMU errors enter both training stages, every earlier
constraint remains, and the future receiver measurement is checked only after
the prediction is saved. The broader component/regression set now passes all
86 checks; the six integration cases complete in 146 seconds on one thread.

The probability calculation uses exact rational checks and outward-rounded
radii. A training-estimated noise scale spends its own part of the same failure
budget; independence between that estimate and later errors is unnecessary.
The bounds are conservative and do not exploit correlation to narrow them.

## What remains assumed

The supplied marginal variance bounds, Gaussian error law and noise-scale
coverage must be justified separately. A floating-point covariance calculation
does not automatically provide proven variance bounds. The software does not
establish aircraft confidence intervals, nonlinear noise propagation, calibration
coverage or scientific significance.

The [exact variance calculation](../ilvis0-joint-variance-bounds/README.md)
provides a checked input path under the stated constant-coupling linear law,
including clock uncertainty. Its 12 checks and all six updated staged integration
cases pass; empirical noise-law justification remains open.

The running eight-minute study is unchanged. Its fixed ±1-metre training
allowance cannot be relabeled as a larger stochastic allowance: previously
conditioned bounds would then need fresh qualification. Any reuse requires a
verified containment argument retaining all earlier constraints.

[Derivation](MATHEMATICS.md) ·
[Combined error operator](../ilvis0-joint-error-operator/README.md) ·
[Prediction-error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md)
