# Receiver derivatives and their uncertainty

The exact-trajectory force calculation is only the first gate. Real receiver
positions are noisy, irregularly timed observations; differentiating them can
amplify errors and correlate successive force estimates.

## Next software stage

Build a separate local-polynomial receiver adapter that returns position, first
derivative and second derivative together with their full joint covariance.
Use actual timestamps and a declared support window. Do not use gyroscopes,
fused navigation, a preferred model or its residuals to choose the window.

Represent differentiation as an explicit linear operator on the original
coordinate observations. Use the complete declared coordinate covariance,
including temporal and cross-coordinate dependence, before solving the weighted
polynomial problem. Keep every coefficient and fail on deficient rank. Retain
position/derivative correlations rather than treating the derivatives as exact.

Known-answer checks must cover exact polynomial motion, irregular epochs,
derivative signs and units, correlated/common coordinate errors, rank loss,
gaps, nonfinite inputs and source immutability. Compare propagated covariance
with an independent matrix calculation; no simulation campaign is needed for
these linear identities.

## Before recorded-data use

- Quantify polynomial truncation on independent curved/accelerating trajectories
  as well as the declared receiver-error model.
- Propagate the joint trajectory uncertainty through the nonlinear force and
  magnitude transformations; state where a local approximation is inadequate.
- Specify how original acceleration increments are averaged and synchronized,
  including finite-rotation effects. Averaging vector magnitudes and taking the
  magnitude of an averaged vector are different operations.
- Define matched acceleration calibration and gravity assumptions without using
  an Earth-model preference to choose them.
- Freeze preselected identities, all candidate comparisons, observable exclusions
  and finite diagnostic limits before any new recorded-data evaluation.

Neither exact-trajectory agreement nor differentiation software checks establish
calibrated observational coverage, gyro-only evidence or a new scientific finding.
No recorded-data optimizer allowance is introduced by this plan.
