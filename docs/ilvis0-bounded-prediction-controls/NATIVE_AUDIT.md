# Native prediction adapter: what transfers and what does not

The existing native adapter preserves all 27 nuisance columns and charges native
calls before execution. It accepts a supplied training-fitted center, uses the
native value and derivative kernels, and does not read Group-1 attitude. Its
earlier six short-path controls checked interfaces, derivatives and training-prefix
agreement. That completed study remains frozen.

Two requirements prevent simply attaching the newly qualified uncertainty
envelopes to those saved outputs:

- **Approximation error:** the old adapter reports the largest discrepancy among
  supplied axis probes. That is sampled local information, not a bound over the
  full nuisance region. The new envelope requires a declared global training
  error norm and future coordinate error bounds. Missing bounds produce an
  unsupported result; the sampled maximum cannot be substituted.
- **Coordinates and covariance:** the old diagnostic builds dense covariance
  factors and converts coordinate errors to metres using the receiver latitude
  and height at each epoch. This is acceptable for its descriptive residual
  report. A new withheld-prediction envelope must instead freeze its coordinate
  representation, error family and transformations before evaluating withheld
  positions. Future observations cannot determine the claimed envelope.

The old prediction worker initializes and fits from training observations and
checks that their predicted prefix agrees with continuous propagation. These
are useful existing safeguards. They do not qualify uncertainty from fitting,
covariance estimation or nonlinear approximation. A new adapter must preserve
those safeguards while exposing training-only dependencies to the structured
forecast and explicitly bounded nuisance calculation.

No old fit is relabeled, no frozen worker is changed and no native evaluation
was needed for this source audit. Native uncertainty qualification remains open.
ESA receiver-only selection and rate-format controls are independent prerequisites
that can proceed without weakening this gate.

Source references: `lll.ilvis0_uncertainty_adapter`,
`lll.ilvis0_uncertainty_geometry`, `ilvis0_prediction_covariance_worker.py`.

[Next qualification steps](NEXT_PLAN.md) · [Software results](README.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
