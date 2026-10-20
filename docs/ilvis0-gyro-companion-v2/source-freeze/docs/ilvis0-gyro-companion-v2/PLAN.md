# Raw-gyro geographic prediction companion

This is a descriptive comparison using the existing 53 saved selections. It
performs no new fit, source decoding or scientific classification. The original
raw gyro plot and all earlier findings remain unchanged.

## Prediction and observations

Compute latitude/longitude rates from consecutive saved primary-receiver fixes,
unwrapping longitude and rejecting unsupported timestamps or gaps over two
seconds. Candidate metrics give the north/east velocity and ground course:
the existing globe metric includes height; the declared disc uses its fixed
radial metric. Keep both courses rather than silently choosing one as measured
aircraft heading. Predict the local frame's transport vector and, separately,
the specified background field. Upstream removal subtracts the same declared
conventional vector for every candidate.

Project onto the aircraft right axis with declared constant roll, pitch and
heading-minus-course. Include the corresponding course-turn contribution for
constant tilt/crab. Actual independent heading, changing roll/pitch, mount
correction and onboard processing remain unknown. Residual motion is not an
independently measured aircraft-pitch correction.

Match retained gyro-bin UTC-second centers to unique receiver-interval centers
within 0.55 seconds. Preserve bin durations, association error and excluded-bin
reasons; no science measurements are interpolated or filled. Read only cached
raw aircraft-axis gyro values and durations, never fused attitude/rate corrections.
Reject unavailable recorded mounting. Compare signed right-axis rates and their
accumulated angles on exactly the same matched support.

Use every selected stretch and preserve source hash, exact interval, record
type, mount-configuration identity, coverage and conservative split/shared-leg
groups. The 53 curves are not independent replications.

## Fixed scenarios

Three candidates; removal fractions 0, 0.5 and 1; constant crab -10/0/+10
degrees; roll -3/0/+3 degrees; pitch -3/0/+3 degrees. That is 243 fixed scenarios
per stretch. The level/zero-crab/zero-removal scenario is the transparent
reference, not a fit. Displayed ranges cover only this finite scenario grid,
not arbitrary aircraft motion or a confidence interval. Do not choose a
preferred scenario or estimate a field magnitude from these comparisons.

## Qualification and finite limits

Before evaluating preserved observations, pass 48 independent known-answer
controls: three candidates, two hemispheres, four cardinal courses and two
removal endpoints. Independently differentiate geographic basis vectors and
project the physical rotation axis; do not use the prediction implementation
to generate its expected answer. Additional unit tests cover tilt/crab, mounting
signs, longitude wrapping, time matching, gaps and fused-channel exclusion.

The observation stage admits all 53 saved selections, at most 1,000 cached
seconds and 1,500 receiver fixes per stretch, and exactly 243 scenarios each.
Reserve identities before execution. Maximum 48 generated controls, 53 observed
summaries, 12,879 stretch/scenario evaluations and 12,879,000 bin/scenario
projections. One worker/four numerical threads, 180 cooperative seconds, no
signals, retries, original reads, native integrations or optimizer starts.
Failed controls block the observed stage. Unsupported observations remain
reported, never silently omitted or retried.

Freeze inputs, code, scenario identities, numerical environment and reference
controls before execution. Publish CSV summaries and a signed observed-versus-
predicted plot, with source/group metadata and explicit motion assumptions.
Relative scatter is descriptive: report no p-value, independent-vote count,
physical-model exclusion or cause of the retained background field.

[Design](../GYRO_PREDICTION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).

## Separate result-schema revision

The first freeze stopped at its first charged software identity because the result
writer supplied identity/kind fields twice. No mathematical result or observation
comparison was persisted. Its charge, source and terminal failure are preserved;
its unused allowance is retired. This separately identified revision changes the
result serializer and adds an actual worker-lifecycle regression test. It has its
own finite allowance above, with all controls requalified for the revised pipeline
before any preserved observations are evaluated. Scientific equations and source
measurements are unchanged.
