# Differentiating receiver positions without hiding uncertainty

The exact-trajectory force diagnostic passes. The next software component now
has **22 passing unit checks** for local receiver-trajectory derivatives and
their joint covariance. These are ordinary mathematical tests, not new
recorded-data fits or calibrated observational coverage.

## What the adapter does

The [derivative adapter](../../analysis/lll/ilvis0_receiver_derivatives.py)
uses actual timestamps, a declared polynomial degree, an explicit gap limit
and the complete supplied coordinate covariance. A scaled singular-value solve
keeps every polynomial coefficient and fails on deficient rank. It does not
choose its support using gyro measurements, a physical-model preference or
fitted residuals.

An explicit linear operator maps the original coordinate samples to position,
first derivative and second derivative. The same operator propagates the
supplied covariance. All nine quantities are kept together, including correlations
between position and derivatives and across coordinates. Their units follow the
input coordinates; latitude/longitude derivatives remain in radians, while
height derivatives use metres.

Original observations are unchanged. The adapter estimates a trajectory; it
does not replace or interpolate the stored science measurements. Angular
coordinate continuity and a justified window-selection policy remain caller
requirements before use on actual geographic data.

## What the checks establish

- Exact quadratic and quartic motion is recovered on irregular timestamps,
  with every coefficient retained.
- A three-epoch second difference has the independently known weights and
  covariance. Correlated-error weighting agrees with an independent matrix solve.
- A common coordinate offset changes position uncertainty, rather than
  incorrectly appearing as a derivative signal.
- Changing coordinate units preserves the physical derivatives and uncertainty.
- Overlapping windows share errors. They cannot be treated as independent
  force observations.
- For the three-epoch stencil with fixed per-epoch noise, halving epoch spacing
  multiplies first-derivative variance by four and second-derivative variance
  by sixteen. A real smoothing-window comparison has additional trade-offs.
- Gaps, unsupported timestamps, invalid covariance and nonfinite results fail
  closed. Polynomial remainder is retained, not silently relabeled measurement noise.
- Propagated covariance retains its mathematical symmetry even where individual
  correlations nearly cancel. The supplied covariance is not modified.

[Tests](../../analysis/tests/test_ilvis0_receiver_derivatives.py) reproduce these
linear identities without original recordings or a simulation campaign.

## What still needs qualification

The covariance assumes the supplied receiver-error model and a correct local
polynomial mean. It does not include polynomial truncation, uncertain covariance
parameters, acceleration calibration or nonlinear transformation error. Real
aircraft motion need not be polynomial over the chosen support.

The completed [error-budget matrix](../ilvis0-channel-error-budget-20261019/INTERPRETATION.md)
assesses approximation and nonlinear response, preserving failed screens and
showing that aggregation matters. Calibration, quantization, synchronization
and a common motion-based support policy still need qualification before a
recorded-data comparison.
