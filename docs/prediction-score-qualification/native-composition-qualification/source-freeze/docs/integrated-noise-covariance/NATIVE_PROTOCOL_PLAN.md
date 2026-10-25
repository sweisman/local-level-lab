# Short noisy native protocol checks

This gate connects the generated inputs, actual nonlinear fitter, continuous
forecast and earlier-only physical-position error calculation. It does not
establish long-duration prediction accuracy or statistical coverage.

Use twelve cases: three generating models, two processing assumptions and two
input laws. Each uses the independently generated two-second, 300 Hz turning
and climbing trajectory, nine queries starting at 0.1 seconds every 0.2 seconds,
six earlier receiver rows, one declared midpoint start and eight fitting
evaluations at most. Preserve all 26/27 calibration columns. Use the existing
reported-short receiver policy and the explicit frozen noise settings in the
shared input constructor. Each model predicts its own generating truth;
these are software controls, not votes between Earth models.

Both gravity and covariance anchors use earlier noisy observations only. Keep
weighting fixed at the declared normalized midpoint. Save the fitted point,
raw forecast and error-conditioned forecast before generating later truth.
Future physical-position errors omit future receiver-error loadings; the same
earlier covariance prefix must be retained. No future receiver coordinates or
quality values may choose an error transform. Hold the last earlier transform.

Check complete accounting, unchanged measured arrays, before-cast residual
binding, native compilation provenance, Gaussian normalization, retained columns,
explicit calibration rank/bounds abstention and both raw and conditional scores.
Keep numerical convergence and the existing 10 m / 30 m accuracy screen as
reported outcomes. Eight evaluations and six training rows cannot guarantee a
unique calibration; a truthful unresolved or rank-deficient outcome is valid
for this interface gate and cannot release observed inference.

## Separate finite allowance

Freeze exact sources, environment and test identities before execution. Per case
prepay at most 1,000 native calls, 10,000 conservative packet steps and 30,000
packet-query visits. Reserve two builds separately. Totals: twelve starts,
12,000 native calls, 120,000 packet steps, 360,000 packet-query visits and a
cooperative five-minute ceiling on one numerical thread. No retries, budget
transfers, original reads or protected reads occur.

Generated construction uses 600 intervals and at most 616 generated samples
per case, including truth used only for later scoring. The increment law uses
10,848 normal variates; the point law uses 7,254. All are reserved before draws.
The twelve cases therefore permit 108,612 variates. Pure interface regressions
have their own finite fixtures and make no native calls.

Only a verified interface result permits freezing the next long-duration noisy
fitting study. Its physical prediction and uncertainty criteria remain separate.

[Nonlinear qualification](NONLINEAR_PLAN.md) ·
[Prediction targets](training-adapter-qualification/README.md) ·
[Shared input generator](rate-point-input-qualification/README.md).
