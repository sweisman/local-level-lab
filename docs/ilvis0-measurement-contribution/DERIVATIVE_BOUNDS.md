# Bounding receiver-trajectory approximation error

All **13 deterministic derivative-bound checks pass**. The existing derivative
adapter remains unchanged. The new helper adds an explicit truncation/error
budget around its position, velocity and acceleration estimates; it does not
infer that budget from small fitted residuals.

Receiver positions are noisy and a local polynomial is only an approximation.
Propagating the coordinate covariance accounts for the declared random errors,
but not the trajectory structure omitted by that polynomial. This distinction
matters because acceleration involves differentiating positions twice.

## A declared derivative envelope

For a degree-\(p\) polynomial centered at \(t_0\), suppose each coordinate's
\((p+1)\)-th derivative is bounded in magnitude by \(M_j\) throughout its
support. Taylor's theorem bounds the omitted coordinate contribution at epoch
\(t_i\) by

\[
r_{ij}\leq M_j\frac{|t_i-t_0|^{p+1}}{(p+1)!}.
\]

If \(H\) is the saved linear operator estimating the nine position/rate/
acceleration components, the corresponding error box is bounded by
\(|H|r\). An explicit coordinate measurement-error box \(e\) contributes
\(|H|e\). The helper also reports the operator's polynomial-reproduction
defect, using declared bounds on lower derivatives; small numerical defects are
not silently set to zero.

All cross-coordinate weights are retained. Latitude/longitude remain in radians
and height in metres, with corresponding derivative units. The helper does not
mix these units into a single norm. Longitude must be consistently unwrapped
within the supported coordinate chart.

## Verification and limits

Independent polynomial and trigonometric trajectories check containment of
known derivative errors. Other controls cover irregular times, sharp coordinate
error boxes, cross-axis weights, an intentionally perturbed operator, invalid
envelopes and extrapolation. These are inexpensive software checks, not new
airborne fits.

The derivative envelope is an **assumption to be justified or stress-tested**,
not a measured bound established by this helper. A coordinate-error box is not
automatically a covariance standard deviation or a calibrated confidence region.
These deterministic bounds do not shrink with an assumed number of independent
samples. Computations retain the reproduction defect but do not constitute a
formal floating-point interval proof.

The next step combines these derivative errors with nonlinear force response,
[time support](TIME_SUPPORT.md), increment quantization, within-packet averaging
and calibration. A wide or overlapping result is retained as uninformative;
the error assumptions cannot be tightened merely to create model separation.

[Implementation](../../analysis/lll/ilvis0_derivative_bounds.py) ·
[Checks](../../analysis/tests/test_ilvis0_derivative_bounds.py) ·
[Derivative/covariance adapter](../ilvis0-channel-trajectory-controls-20261019/DERIVATIVES.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
