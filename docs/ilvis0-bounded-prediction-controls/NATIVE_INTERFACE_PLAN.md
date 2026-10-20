# Training-only structured prediction interface

The next component adapts supplied native predictions and derivatives to the
qualified bounded-prediction calculation. It performs no integration or fitting.
It replaces neither the native kernels nor their completed controls.

Use one explicitly frozen affine coordinate frame and one shared covariance/
scale family for every physical candidate. The frame is defined by configuration,
not recalculated from withheld positions. Do not silently wrap longitude or drop
an unidentified parameter. Preserve the declared parameter order and drift time
origin/span. The interface accepts training observations and future **predictions**;
there is no future-observation argument.

For fitted center `theta0`, form training residual `y - f(theta0)` and use
parameter displacement `theta - theta0`. Shift the entire original parameter box
by that center. In the future, add `f_future(theta0)` to the conditional error
prediction and retain `J_future - A J_training` as the nuisance directions.
Native Jacobians learned from training data always use the conservative full
training-noise dimension, not the fixed-design rank shortcut.

Approximation allowances must identify the candidate, full parameter box,
center, frame and shared-error configuration. They must apply globally over
that box: local samples are not accepted as global bounds. Missing allowances,
including a missing covariance alternative, produce an unsupported envelope.
Externally declared global allowances are still assumptions; the interface
cannot prove them or establish observational coverage.

Component tests use independent affine means and bounded nonlinear mean errors,
nonzero fitted centers, 27-column rank loss, two covariance alternatives and
deliberately mismatched identities. Check training/future coordinate transforms
against separate matrix calculations and verify that future observations cannot
enter the API. No archive reads, optimizer starts or native integrations occur.

The global native remainder provider and empirical shared-error assessment
remain separate gates before a new observed prediction study.

[Mathematics](MATHEMATICS.md) · [Native source audit](NATIVE_AUDIT.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
