# Bounds to qualify before native prediction

These equations describe an assumed Gaussian error family with explicit
deterministic model-error bounds. They do not establish those assumptions for
airborne observations. The native adapter and its global remainder treatment
remain unqualified.

## Shared scale

For one covariance alternative, let a fixed calibration reference satisfy
\(z=Xb+e+s\eta\), with \(\eta\sim N(0,I)\) and \(\|e\|\leq B\).
Project away the fixed reference design and call the observed residual norm
\(R\). If its residual degrees of freedom are \(\nu>0\), then

\[
s\leq s_+=\frac{R+B}{\sqrt{\chi^2_\nu(\alpha_s)}}
\]

except on a lower-tail event of probability \(\alpha_s\). The reference
coefficient bounds cover any numerically discarded design response. No
positive degrees of freedom, unknown remainder, or an adaptively learned
reference design means no scale bound is supplied.

This reference is shared across physical candidates. Re-estimating its scale
from each candidate's own errors would be a different method. No independence
between the shared calibration and later training events is required for the
error-budget union bound.

## Bounded nuisance region

In whitened candidate training coordinates, retain every parameter column.
Write the retained numerical decomposition as \(X_r=U_rS_rV_r^T\). Bound
\((X-X_r)b\) over the entire declared parameter box and add that bound to
the training remainder. Then

\[
\|S_rV_r^T(b-\hat b)\|\leq
s_+\sqrt{\chi^2_k(1-\alpha_b)}+B_{\rm total}=\rho.
\]

For a fixed design, \(k=r\). For a Jacobian learned from the same observations,
use \(k=n\), the full training-noise dimension: its projection depends on the
noise and cannot claim a fixed-rank chi-square distribution. Zero-rank designs
retain the whole parameter box rather than zero uncertainty.

For a prediction direction \(l\), separate its row-space and null components.
The row-space support is bounded by
\(l^T\hat b\pm\rho\|S_r^{-1}V_r^Tl\|\). Add the null component's support
over the original box, then intersect with the full-box support. This is an
outer bound; it does not assert that every point in the resulting rectangular
prediction region is jointly feasible.

## Conditional prediction and deterministic error

Let \(A=C_{pt}C_{tt}^{-1}\). For approximate training/future means \(X_tb\)
and \(X_pb\), the prediction center and nuisance directions are

\[
c=Ay_t,\qquad D=X_p-AX_t.
\]

Known intercept terms are included consistently before whitening. Conditional
future noise is Gaussian with covariance
\(C_{pp}-C_{pt}C_{tt}^{-1}C_{tp}\). For \(m\) prediction coordinates, the
simultaneous marginal noise allowance uses
\(s_+\Phi^{-1}(1-\alpha_p/(2m))\sqrt{v_i}\). Bonferroni requires no
coordinate independence.

If \(\|L_t^{-1}e_t\|\leq B_t\), the additional conditional-mean error is
bounded coordinatewise by
\(B_{p,i}+\|(A L_t)_{i,:}\|B_t\). The structured forecast calculates these
response norms without a dense cross-covariance. Omitting the training-remainder
term would understate uncertainty.

## Family and selection limits

Allocate \(\alpha_s+\alpha_b+\alpha_p\) before evaluation. Under the stated
assumptions this bounds false interval exclusions without relying on independence
of the three events. Union the envelopes across the predeclared covariance
family; if the true member belongs to that family, its valid envelope is retained.
Unsupported alternatives are not silently dropped.

The bound is not a coverage claim conditional on passing a convergence,
selection or adequacy gate. An unsupported calculation abstains; abstention
frequency must be reported. Software coverage controls count unsupported outputs
as failures rather than allowing an always-abstaining method to qualify.

Finite-family sensitivity does not cover arbitrary unmodeled dependence.
Nonlinear remainder limits must hold over the declared parameter region;
saved axis probes cannot prove that. These equations supply no production
decision threshold or calibrated significance for the existing 53 preferences.
