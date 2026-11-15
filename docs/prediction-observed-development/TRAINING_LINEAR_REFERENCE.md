# The small ESA training error is not explained by parameter count

This saved-only check uses the same first **600 receiver reports** from the ESA
development recording. It reads the two completed fits and the already verified
training-error calculations. It runs no optimizer and reads no later receiver
positions or reserved flight groups.

| Declared IMU error law | Fitted calibration directions | Whitened error sum | Local linear reference |
|---|---:|---:|---:|
| Increment | 26 of 26 | 7.148 | 1,774 |
| Point | 26 of 26 | 7.148 | 1,774 |

There are 1,800 training coordinates. Both fitted Jacobians have rank 26 at the
stated relative cutoff of `1e-8`, and neither fit is at a calibration bound.
Each saved residual reproduces its fitted cost exactly and is almost
perpendicular to the 26 local calibration directions. Under a **correct fixed
Gaussian error covariance and a linear fitted mean**, the expected whitened
error sum after fitting those directions would be 1,800 − 26 = **1,774**.
The actual sum is about **0.4%** of that reference. Fitting 26 directions out
of 1,800 does not explain the very small training error in this local model.

This is an error-model diagnostic, **not a calibrated statistical rejection**:
the aircraft fit is nonlinear, and this calculation does not establish the
sampling distribution of its fitted cost. It also cannot determine whether the
current covariance is too broad, the recorded errors share unmodeled structure,
or another assumption needs revision. The separate
[training-innovation check](TRAINING_INNOVATION_RESULT.md) finds that height
errors remain correlated after the declared whitening. Both findings support
revising and qualifying the observed error law before making a coverage claim.

The [saved calculation](training-linear-reference.json) records the source and
study hashes, both ranks, costs, singular-value ratios and local residual
projections. Three deterministic tests check the calculation. The scientific
decision remains **abstain**.
