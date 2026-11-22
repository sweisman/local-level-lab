# Receiver likelihood for long recordings

The legacy receiver-only covariance and projection helpers grow with the
square of the number of position reports. An eight-hour ESA recording has
64,080 reports, so a dense three-coordinate matrix would require hundreds of
gigabytes. The main motion-fitting class already accepts the shared
`LinearInnovations` operator for structured errors. This software check maps
one declared receiver-only law to that common operator and exercises all
residual and nuisance columns at the recording's full receiver count.

## Proposed software gate

Keep the present dense calculation as the small-problem reference. Use the
existing state-space whitening operator for the same declared receiver law:
per-epoch reported 3×3 covariance and white noise, exponentially correlated
noise, a shared offset, and a shared linear drift. Map each receiver
latitude/longitude/height residual to local north/east/up with the *same*
declared coordinate metric before whitening. For excluded coordinates, use
their marginal covariance; do not simply drop already-whitened rows.

The exponential component is a Markov state. At each actual receiver time,
predict its state covariance, compute the innovation covariance, whiten the
innovation by its small Cholesky factor, and update the state. Carry the
offset and drift as static latent states. Apply the resulting **fixed linear
filter** to every nuisance Jacobian column as well as the residual; the
Jacobian must not receive a separately estimated filter. Do not interpolate
gaps or estimate the covariance from the same residuals in this software gate.

Before any observed long-recording fit, require:

1. Small exact examples matching the existing dense whitened residual,
   Jacobian, objective and gradient for full, horizontal and height-only
   coordinates under identical covariance inputs.
2. Known-answer generated histories with correlated noise, cross-axis formal
   covariance, irregular times and a low-frequency offset/drift. Include
   invalid covariance and time-order rejection.
3. A bounded 64,080-report runtime/memory benchmark with finite input and
   output hashes. Report peak memory and wall time; no model decision is
   involved.
4. A separately frozen matched observed development fit, changing only the
   computation of the same covariance. Agreement with the dense reference on
   a short common prefix must precede any long fit.

The state-space operator is a computational representation of an **assumed**
receiver error law. Numerical equivalence cannot establish that the law
describes aircraft errors or calibrate forecast coverage. Preserve all
existing frozen studies and their dense calculations.

The [software result](STRUCTURED_RECEIVER_LIKELIHOOD_RESULT.md) records the
small checks, generated histories and full-length runtime benchmark. A
[one-call native check](STRUCTURED_RECEIVER_NATIVE_RESULT.md) confirms the
same whitening for all 26 physical derivatives on an actual training prefix.
The [matched two-fit comparison](STRUCTURED_RECEIVER_FIT_RESULT.md) then
passes the computational substitution gate on that prefix. The assumed
error law still needs aircraft adequacy and prediction checks.
