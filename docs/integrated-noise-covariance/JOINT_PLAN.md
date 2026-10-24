# Preserve noise shared by a query and packet endpoint

The native step derivatives are qualified. Complete-history propagation also
needs a covariance operator that preserves the dependence between a partial
position query and the endpoint driven by the same measured increment.

Add an explicit joint-observation mode to the existing shared innovations
component. For previous state x, independent standard drivers z and e, declare

```text
observed error = H x + D z + R e
next state    = F x + B z
```

The same z appears in both equations. The existing after-transition mode must
keep its meaning and remain the default. It is the special case with observed
loading H_after F and shared loading H_after B. Bind the mode into checkpoint
configuration and reject schema/column mismatches.

Construct the innovation covariance and the cross-covariance with the endpoint
from these shared loadings. Use the generalized Joseph update, retaining
positive-semidefinite covariance through loading products, without jitter or
eigenvalue clipping. Apply the same transformation to vectors and all 27 matrix
columns. Future means and marginal covariance must still use earlier errors
only; unknown later innovations remain random.

Compare with independent dense driver-to-observation matrices and Gaussian
conditioning. Include a packet example with a partial displacement and endpoint
sharing one increment, as well as changing transitions, cross-axis observation
noise and positive/negative shared couplings. Demonstrate that making the
shared noise independent produces a different, incorrect covariance.

Retain all 46 earlier controls. The eight new controls use at most eight
generated epochs; the existing 64,080-epoch storage case stays unchanged.
Use one numerical thread, with no random draws, native calls, fits, original
reads or protected reads. Preserve earlier source snapshots and require a
fresh source/environment-bound qualification before publishing this extension.

This qualifies covariance algebra. Composing the actual native packet
derivatives over complete histories, adding persistent receiver errors and
including fitted-calibration uncertainty remain separate gates before aircraft
fitting. Existing accuracy limits and failed noise controls remain unchanged.

[Component overview](README.md) · [Native step](../native-noise-linearization/README.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
