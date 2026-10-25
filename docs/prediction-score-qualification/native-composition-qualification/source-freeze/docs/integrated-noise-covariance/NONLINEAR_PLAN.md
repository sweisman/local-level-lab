# Next gate: noisy calibration and later-position prediction

The fixed-error adapter and efficient work accounting are software-qualified.
The next gate tests the complete nonlinear estimator. It must not substitute
component checks for accurate withheld predictions or calibrated uncertainty.

## Match the generated input to its error model

Keep recorded-increment errors and rate-point errors separate. The earlier
failed noisy study generated continuous white noise and integrated changing
bias directly into increments. Preserve that study and its results.

For rate samples converted by the trapezoidal rule, generate noise at the sample
points first. Neighboring intervals share an endpoint. Sampled changing bias
must also be integrated by that same rule; it is different from an exact
continuous-time bias integral. Qualify this independent generator against
closed-form sample covariance and prefix-reproducibility controls before fitting.
Point variance is an explicitly supplied squared-rate quantity, not a hardware
specification or an automatic conversion from continuous white-noise PSD.

Reserve all generated random variates before drawing. Use separate named
streams for each sensor, white noise and changing bias. Extending the later
record must preserve the earlier generated inputs exactly.

## Qualify the complete prediction path

First qualify short generated cases with all 26/27 calibration columns, each
physical candidate, both processing assumptions and both input laws. Fit only
earlier noisy measurements, freeze covariance from their declared midpoint
anchor, and preserve Gaussian normalization. Keep raw forecasts separate from
earlier-error-conditioned forecasts. Score later physical truth only after
both forecasts and their calibration binding have been saved.

Distinguish prediction targets explicitly. A future receiver measurement includes
receiver white noise, persistent offsets and drift; a noiseless physical position
does not. Earlier receiver errors contribute to both conditioning problems, but
must not be added to the physical-position target. Carry the receiver state
continuously while removing only its future observation loadings for that target.
Hold future receiver transformations at the last earlier value under a named
policy; do not derive them from withheld coordinates. Keep the training covariance
prefix exactly unchanged. A singular future innovation is unsupported by the
current full innovations interface and must fail without a variance floor.

Report numerical completion, actual prediction errors, unidentified directions,
active bounds and unsupported uncertainty separately. A linear correction
outside the permitted calibration box receives no unrestricted covariance.
Intervals from an interior linear approximation are diagnostic until nonlinear
coverage is independently tested.

Then freeze a finite long-duration study. Keep the existing 10 m horizontal /
30 m height RMS accuracy screen, along with its maximum-error checks. Reserve
the exact starts, seeds, source/environment versions and native/packet work
before launch. Do not increase noise allowances or calibration bounds after
seeing outcomes. No aircraft measurements or protected flight groups enter
these software gates.

The initial source-law gate permits at most 24 new deterministic checks plus
affected noise regressions, one thread, zero native builds/calls and no optimizer
starts. Random samples occur only in explicit finite test fixtures with a
precharged variate count. The native fitting matrix and long-run resource
definition require their own subsequent freezes; this page does not release
an unbounded campaign.

[Training adapter](training-adapter-qualification/README.md) ·
[Work accounting](prepaid-native-qualification/README.md) ·
[Earlier noisy failures](../esa-noisy-prediction/INTERPRETATION.md) ·
[Prediction protocol](../PREDICTION_VALIDATION.md).
