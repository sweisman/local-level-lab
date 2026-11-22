# The ESA training errors still have a height pattern

This check uses **only the first 600 receiver reports** from the ESA
development recording. It rebuilds each declared error law, verifies the
original fitted cost and covariance calculation, then asks what pattern
remains after whitening the fitted training errors. No fit was repeated.
Later receiver positions and the seven reserved flight groups were not read.
Both prespecified laws passed the technical replay.

| Whitened fitted error | RMS, increment law | Correlation one report apart | Correlation 20 reports apart |
|---|---:|---:|---:|
| North | 0.0618 | 0.190 | −0.022 |
| East | 0.0462 | 0.366 | −0.015 |
| Height | **0.0772** | **0.825** | **0.538** |

The point-sampled IMU error law produces virtually the same numbers. The
overall whitened RMS is **0.0630** under either law. A correctly specified
fixed covariance with a known mean would yield roughly unit-scale,
uncorrelated innovations. Here the height error remains strongly persistent
even after the declared covariance calculation. The very small RMS also
shows that this covariance is large relative to the *fitted training*
residuals.

This is a **diagnostic warning**, not a formal statistical rejection. The
same 600 reports estimated 26 calibration parameters, so standard white-noise
reference limits cannot be applied to their fitted residuals without a
separate full-fit known-answer calibration. The result does not identify
whether the mismatch comes from IMU error, receiver error, aircraft motion,
calibration or another assumption. It does show that the two current laws
provide nearly identical training diagnostics while both later forecasts
miss height ranges; choosing between them by training score would not solve
the observed prediction problem.

The [frozen plan](TRAINING_INNOVATION_PLAN.md) and [saved report](training-innovation-result.json)
record the exact inputs, source and completion hashes, replay checks and both
laws. The study closed 2/2 tasks with no errors or active locks. A calibrated
error-law adequacy rule still requires passing generated full-fit controls and
an independently justified model for the observed changing error. The first
[complete-fit generated pilot](FULL_FIT_INNOVATION_NULL_RESULT.md) converged
numerically but failed its physical trajectory screen. No Earth-model decision
follows; the scientific decision remains **abstain**.

The [local fit projection control](LOCAL_PROJECTION_NULL_RESULT.md) found that
fitting the saved 26 directions to white error does not reproduce the height
pattern. A [saved error-pattern audit](INNOVATION_MORPHOLOGY_RESULT.md) maps
all 120 lags and shows that most remaining height variation is slow. Neither
check identifies the physical cause or qualifies forecast uncertainty.
