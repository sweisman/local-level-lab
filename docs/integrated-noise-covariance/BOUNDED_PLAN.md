# Next gate: keep uncertainty at calibration limits

The [saved calibration check](../structured-noisy-diagnosis/INTERPRETATION.md)
finds accurate short forecasts with strongly coupled calibration parameters.
An unrestricted Gaussian parameter covariance is unsuitable when estimates
reach their allowed limits.

Reuse the existing `ilvis0_bounded_prediction.Region` and `predict` calculation.
Add a small adapter accepting the accumulated-error `LinearInnovations`
operator, all earlier residuals, every mean-design column, a bound for every
coefficient and an explicitly supplied scale/remainder policy. Future receiver
observations are not inputs. Keep the physical-position target distinct from
a future receiver-measurement target in the upstream operator.

Compute the conditional error mean and covariance with the existing state-space
operator. Propagate the effect of earlier whitened errors with a state-sized
square-root recurrence, avoiding a dense whole-record covariance or projection.
Project every parameter column through the same earlier-only operator. Retain
null directions through the full coefficient box rather than deleting them.

Qualify against independent small dense calculations: exact-bound parameters,
rank-deficient calibration, correlated errors, both observation-timing forms,
parameter-unit changes and shared training/future errors. Missing nonlinear
remainder allowances must return unsupported. A supplied zero allowance is
appropriate for exact linear software fixtures; it does not certify a nonlinear
aircraft reconstruction.

The initial software allowance is at most 24 deterministic adapter checks plus
the affected existing bounded/state-space regressions, one numerical thread,
two minutes per test group, zero native builds/calls and zero optimizer starts.
No archive measurements, protected flights or random draws are required. Any
subsequent native connection or nonlinear coverage study needs a separate freeze.

Passing this interface gate will not relabel the completed short fits, qualify
the earlier twenty-minute failure or release further observed-data fitting.
