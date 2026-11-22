# Test which GPS differences can be modeled separately by receiver

The [receiver substitution](ESA_FORECAST_RECEIVER_TRANSFER_RESULT.md)
showed that the same forecasts and uncertainty model give different error
reference outcomes across three GPS solutions. Use the signed position
differences already archived for the eight windows to test whether a
covariance specific to each receiver explains the differences.

Analyze the paired differences `mosaic03 − air1` and `pwrpak7 − air1`
together. Under a receiver-specific model with uncorrelated errors, these
differences share the `air1` covariance. The two diagonal blocks also
include the covariance of their respective alternate receivers. This
constrains the shared block to be symmetric and each inferred receiver
covariance to be positive semidefinite. Shared antenna, processing and
satellite errors that cancel in both differences remain unobservable.

Use the same four omitted pairs as the forecast comparison. In each
120-report window, use orthonormal cosine coefficients in three fixed
frequency ranges at the approximately one-second cadence. Retain the
constant coefficient separately. Use bands with upper edges 0.05, 0.25
and 0.5 Hz. Require all matched times and check the cadence. Pool only
the six donors in each fold. Compare an unrestricted covariance for the
six difference channels with the structured covariance. For the
structured estimate, symmetrize the cross block, subtract it from the
two diagonal blocks, and clip negative eigenvalues of the three inferred
receiver matrices at zero. Record those eigenvalues before clipping.
Use the same trace-scaled ridge of one millionth of mean variance for
both fitted covariance matrices.

Seal the donor fits before scoring the two omitted windows. Report
normalized Gaussian log scores by band and the change in each fold.
Per-coefficient scores compare covariance estimates. Adjacent modes and
windows within the flight may be dependent, so the totals are descriptive.
Keep the independent-receiver estimate as a candidate for further tests
only if the unrestricted law beats the isotropic covariance and the
structured score is within one percent of that gain. The isotropic reference
uses the same donor mean variance and ridge. An independence failure
calls for a joint receiver term. No outcome estimates common errors,
changes the aircraft forecast covariance, or opens reserved flights.

Freeze the prior score archive, fixed comparison code, named tests,
environment and signed point-convention receiver offsets. Use four
disjoint tasks on two one-thread workers, at most 24 bound calls and 72
bound steps per task and a 180-second cooperative wall allowance. Use
the qualified shared recovery process, with one additional attempt per
unfinished task and a separate 180-second recovery allowance.
