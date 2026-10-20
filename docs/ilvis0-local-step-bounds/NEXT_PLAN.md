# Close geographic propagation and endpoint observations

The supplied-context local-step matrix is complete. Preserve its sources and
allowance. The next separately identified component must mirror the complete
predictor/corrector in the native kernel, not a different integration scheme.

## Preserve scalar physical domains

A global norm radius is a symmetric outer relaxation. At a fitted removal
fraction of zero, a true physical interval [0,1] needs change radius one; that
outer ball also contains negative fractions. Checking the relaxed ball itself
as the physical domain would incorrectly reject this legitimate boundary case.

Keep declared scalar intervals separately from their change/remainder radii.
Validate the actual interval and center, then propagate the conservative norm
bound. Qualify boundary-centered removal and period intervals explicitly.
Preserve the completed local component unchanged; revised interfaces need a
new source identity.

## Geographic predictor/corrector

Represent latitude, longitude and height as separate scalar bounds with their
declared units. Do not mix radian and metre uncertainties into an unexplained
single coordinate norm. Keep longitude continuous; do not silently wrap it.

1. Compute candidate coordinate rates from the old position and velocity.
2. Form midpoint coordinates using those rates and half the interval.
3. Form transport using midpoint latitude and the **old rates**, then evaluate
   the first local step to obtain its velocity estimate.
4. Recompute rates at the same midpoint coordinates using the average of the
   old velocity and that estimate.
5. Recompute transport with these rates and midpoint latitude. Evaluate the
   second local step from the original attitude/velocity, not from the first
   local step's endpoint.
6. Update coordinates with the recomputed rates and the full interval.

Use the kernel's declared globe/disc metrics. Scalar inverse and metric-power
bounds must cover the complete state region and reject denominator/domain
crossings rather than clip them. Sine/cosine propagation must retain both actual
change and first-order approximation error. Report conservatism and unsupported
domains; passing a short control need not imply useful long-record precision.

## Lever arms and time

For endpoint observations, rotate the body lever arm by the predicted attitude,
apply the candidate coordinate metric at the predicted IMU position, and add the
offset as the kernel does. Do not substitute fused attitude or receiver truth.

A later extension can propagate a bounded integration period and correspondingly
scaled raw increments for observations inside one packet. Preserve their shared
fraction and cross terms. A time interval crossing packet boundaries requires
separate support/union handling; it is not covered by a single local tangent.
Long-record arithmetic and shared observational covariance remain separate gates.

## Qualification

First test scalar/domain operations and full predictor/corrector values against
independent formulas, including nonzero parameter centers and supported physical
boundaries. Then freeze finite end-to-end generated cases and a separate unchanged
C-kernel harness. Compare values, directional derivatives and global remainder
radii for all candidates, both hemispheres, lever arms and timing scopes.
Retain all original nuisance directions; identify fixed timing explicitly.

No observed prediction allowance follows from this plan. The existing archive
findings, old failures and protected ESA groups remain unchanged.

[Completed local controls](INTERPRETATION.md) ·
[Prediction interface](../ilvis0-bounded-prediction-controls/NATIVE_INTERFACE.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
