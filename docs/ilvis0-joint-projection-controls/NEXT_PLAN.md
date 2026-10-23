# Certified error bounds for fixed training summaries

The inverse, transpose and projected-covariance operations pass their independent
reference and long-record checks. The [four-law error comparison](../ilvis0-summary-error-controls/README.md)
has also completed: all four cases cover twelve training summaries and 441 later
coordinate errors in one declared error budget. The signed nonlinear-row
arithmetic passes local tests, retaining all calibration columns and rounding
allowances. A complete prediction qualification has not yet followed.

The [saved native-binding check](../ilvis0-training-summary-controls/README.md)
also passes all six cases, reproducing 180 original coordinate inequalities and
auditing 144 signed-summary inequalities without integration.

**Running:** the separately frozen
[complete-cadence training-bound stage](../ilvis0-dense-physical-bounds/README.md).
All six
[data-independent starting bounds](../ilvis0-dense-physical-roots/README.md) and the
[six-history reuse comparison](../ilvis0-native-prefix-format-recovery/README.md)
now pass. The requirements below remain the acceptance rules; passing
variance arithmetic and input connections alone is insufficient.

Use twelve fixed rows: four time-polynomial summaries on each physical axis.
Choose weights from timestamps only, independently of observed values, fitted
models and residuals. Keep every physical calibration parameter when applying
these summaries to predicted measurements.

## 1. Projected variance: software checked

Extend the shared constant-coupling variance library. For arbitrary signed row
weights, retain white error, shared offset/drift, correlated receiver error and
accumulated acceleration/gyro error, including cross-axis covariance.

White and offset/drift terms can use exact rational arithmetic. Accumulated
noise admits an exact polynomial construction: a weighted acceleration error
has kernel `sum w_i (t_i − s)`, while a force-coupled gyro error has kernel
`sum w_i (t_i − s)² / 2`, for epochs after `s`. Integrate their covariance
products over the intervals between epochs, retaining the fixed noise origin.

Use a certified exponential recurrence for the receiver's correlated component,
with outward rounding at bounded-precision steps. Do not substitute marginal
variances or assume independent epochs. Treat common clock uncertainty explicitly:
stationary receiver lags are unchanged; drift variance has a convex endpoint
bound; a common forward time shift adds a nonnegative prefix contribution to
the constant-coupling accumulated-noise variance.

Preserve the parent covariance identity and record a separate projection identity
for weights. Verify single/signed rows, exact offset cancellation, drift anchors,
cross-axis terms and clock endpoints against independent analytic cases and the
matrix-free reference. Unsupported arithmetic must remain unsupported.

## 2. Simultaneous error budget: four-law comparison complete

Extend the Gaussian-allowance interface to explicitly declared linear rows,
while preserving the old epoch-coordinate interface. Reuse the existing rational
tail certificate and outward square-root arithmetic. Match the same parent
covariance identity and shared scale bound. Correlation between rows, epochs
and the scale assessment does not justify resetting their failure budget.

A finite software comparison can use four previously declared law combinations:
two receiver correlation times and two example gyro noise levels. For each law,
include all twelve training summaries and the 147 declared later epochs in one
error-budget family. This checks the error interface, not the actual noise of
the instruments or the complete nonlinear trajectory.

## 3. Bind summaries to nonlinear predictions: next gate

Generalize the declared-training-row arithmetic to verified signed combinations
of saved native centers, coefficients and remainder bounds. Retain all 27
physical parameters and the complete source-expression layout. Check matching
source, times, scales and basis identities. Unshared remainders require absolute
weight bounds; they cannot be canceled as though their signs were known.

The interface must cover the source box and its saved reference center. Rounded
projected coefficients need an explicit error allowance over the full box. A
unit-row projection must reproduce the existing coordinate inequalities exactly.
Keep the error-family identity attached when selecting its twelve training radii;
do not allocate a new probability budget after observing which rows are useful.

Local checks cover the original 51-column layout and the lifted 78-column layout,
signed remainder bounds, exact coefficient-rounding allowances and 289 training
epochs. The six sealed generated sources now pass using their actual saved
native centers, Jacobians and training reports. Their five original training
epochs remain a binding control, not the new complete-cadence problem.

Only after those saved bindings pass should the complete-cadence native-bound
comparison be costed. Repeated native prefixes are a known performance issue;
qualify reuse against cold runs before using it, or freeze the full cold-run cost.
Keep every later observation excluded during either preparation.

### Keep each bound tied to its error assumptions

The saved five-observation bounds use a deterministic one-metre error premise.
They remain binding controls; they cannot become bounds for the new Gaussian
noise cases merely by attaching different error radii. Data-independent bounds
over the same physical calibration box can be reused. A bound tightened using
training data needs a verified chain back to that experiment's observations,
error family and earlier bounds, with no circular dependencies.

Before the dense experiment launches, check those links explicitly: source and
frame, calibration box, training-observation hash, conditioning-input hash and
the single 453-row error family. Reject old one-metre conditioning carried into
a different noise case. The generated cadence has 289 earlier epochs; it must
not be relabeled as the separate 292-epoch retrospective aircraft protocol.

The shared `lll.ilvis0_prediction_lineage` guard now checks this metadata chain
for the current 51-column fixture. Each new stage must retain the parent
constraints and domains that made its bounds valid. The fingerprint includes
the complete error-allowance certificate: covariance identity alone cannot
authorize a changed confidence, scale or radius assumption.

Twelve local lineage cases pass, including stale proofs, circular reuse, changed
observations and dropped parent constraints. Numerical interoperability with the
complete-cadence error library now passes, including the actual 453-coordinate
allowance certificate. These checks do not verify inequality
arithmetic, native bound validity or empirical coverage, and do not qualify the
78-column conditioning path or an aircraft prediction.

The shared `lll.ilvis0_dense_training` builder now connects these pieces in one
fresh input bundle. It derives weights from timestamps, preserves every typed
parent constraint and binds the complete 453-row error premise. It rejects
legacy one-metre rows rather than silently retaining them under a different
noise label. All 44 row/lineage connection tests pass, including the actual
dense error family and a second stage retaining its parent's constraints. This
qualifies the input connection, not native prediction or observational coverage.

Only after these controls qualify should a separately costed complete-cadence
comparison be frozen. Preserve the five-observation counterexample and all old
width targets. New training information and a different declared error family
must be identified as a different problem. Neither device bounds nor acceptance
rules may be tightened to favor a model.

Whole-period mean predictions, native approximation/clock treatment and empirical
error-law adequacy remain open. This plan provides no new observed fit, production
decision or protected ESA confirmation use.

[Completed operations](README.md) · [Error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
