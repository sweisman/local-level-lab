# Simultaneous allowances with correlated errors

Declare the complete set of \(M\) scalar training and future errors before
looking at future observations. Assume zero-mean Gaussian marginal errors with
\(\operatorname{Var}(e_i)\leq\sigma^2 v_i\). The fixed supplied \(v_i\) are variance
upper bounds; correlations may be arbitrary. A separate scale assessment gives
\(\Pr(\sigma>U)\leq\alpha_s\).

The Gaussian Chernoff bound and union bound give

\[
\Pr\left[\exists i: |e_i|>\sigma c\sqrt{v_i}\right]
\leq 2M\exp(-c^2/2).
\]

For \(x=c^2/2\geq0\), define
\(S_{256}(x)=\sum_{k=0}^{256}x^k/k!\).
Every term is nonnegative, so \(S_{256}(x)\leq\exp(x)\) and
\(2M/S_{256}(x)\) is a conservative upper bound on that failure probability.
The implementation chooses an integer \(c\) from the finite grid 1–64 and checks
\(2M/S_{256}(c^2/2)\leq\alpha_e\) using exact fractions. No rounded normal
quantile is needed. Unsupported counts/probabilities fail explicitly.

On the event that both bounds hold, all errors satisfy
\(|e_i|\leq Uc\sqrt{v_i}\). Its failure probability is at most
\(\alpha_s+2M/S_{256}(c^2/2)\leq\alpha_s+\alpha_e\).
This union argument needs no independence between \(U\) and the errors, or
between the errors themselves. The noise scale must still have its stated
coverage; a fitted residual standard deviation is not automatically such a bound.

Each returned radius uses an exact upper square root of the supplied binary64
variance bound and an outward endpoint of the exact product. This checks radius
arithmetic, not the earlier calculation of those variance bounds.

Use training rows as the staged method's declared allowances. Add the future
rows to the corresponding latent-position prediction ranges when assessing
future receiver observations. A latent-trajectory interval alone is not an
observation-error interval. Coordinate identities, the integration origin and
the complete probability budget must remain aligned across both periods.

For receiver plus IMU error, the linear Gaussian approximation must account for
the dependence introduced by integrating noisy IMU inputs. Nonlinear effects,
mean shifts, changing flight dynamics and covariance-family selection cannot be
silently absorbed into this proof. The existing calibration, approximation and
arithmetic requirements remain separate.

[Software scope](README.md) · [Full V01 requirements](../ilvis0-long-staged-feasibility-v2/V01_GATES.md)
