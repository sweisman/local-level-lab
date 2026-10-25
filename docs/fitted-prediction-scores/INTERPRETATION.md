# What the fitted-prediction scores show

The saved-data calculation is complete. It preserves all 24 generated starts:
20 pass their original numerical checks, and four remain failed. Ten of the
twelve training-selected comparisons are available; two have no qualified start.

Among the available primaries, the largest later coordinate error is 5.29–6.25
times the stated conditional noise standard deviation. The score checks the
complete later block, with latitude, longitude and height in consistent units.
It does not select a favorable time or a better-looking start.

That ratio is not a confidence level or the probability that a model is wrong.
It takes a maximum over correlated measurements, and the noise allowance treats
estimated calibration as known. The calculation therefore cannot stand in for
uncertainty from the complete fitting procedure.

Each case was generated under its named model and fitted using that same model.
These are software checks, not another comparison of Earth shapes. They also
share one noise seed, so they cannot establish a tail quantile or coverage rate.

The next step uses fresh realizations of the same declared noise laws, with
calibration estimated anew for each one. The [draw-separation plan](../prediction-score-qualification/INDEPENDENT_DRAWS.md)
keeps covariance assumptions fixed while changing seeds. Independent calibration
and validation draws require their own finite freeze before new fits.

No aircraft findings, physical accuracy limits or reserved ESA groups change.

[Full saved report](README.md) · [Method](PLAN.md) · [Next analyses](../NEXT_STEPS.md).
