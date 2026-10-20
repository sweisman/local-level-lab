# Whole-history acceleration-only necessary constraints

## Fixed data and selection

Reuse the two hash-sealed delta-velocity/receiver caches from the completed
snapshot assessment. The original IMU8 and IMU21 stretches and every previous
result remain unchanged. This is retrospective development, not independent
confirmation. No original file is decoded again and no new recording is selected.

Partition each cache into consecutive groups of exactly 200 packets from its
original first interval. Keep identical packet indices under nominal 5 ms and
header-interval hypotheses; do not restart the nominal clock at a group boundary.
Publish every group, including a partial tail, with eligibility/rejection reason.
Reject groups outside the saved stretch under either clock or lacking a complete
±16-second receiver stencil inside that stretch. Eligibility uses only timing
and support, never gyros, force values or candidate residuals.

The preparation inventory fixes exact identities before force evaluation. Keep
all unsupported groups, receiver gaps, derivative-envelope conflicts and physical
domain failures. Do not search replacement groups or change selection after results.

## Common assumptions and averaging

Keep the snapshot's degree-four polynomial, fixed identity regression weights,
1 m/5 m receiver-coordinate boxes, Taylor derivative envelopes, apparent gravity
9.70–9.90 m/s², one-count delta-velocity bound, empirical IMU8/IMU21 scales,
±0.15-second common clock offset, body-force direction rate ≤1 rad/s and scalar
magnitude rate ≤2 m/s³. These are explicit hypotheses, not verified specifications,
calibrated confidence regions or an inferred noise floor. Their unchanged values
are recorded in the source freeze and the preceding plan.

At each packet group's center, estimate the receiver coordinate jet with the
same ±16-second support policy. Carry measurement and trajectory-truncation
bounds through the nonlinear force calculation for every candidate. Bound its
continuous group average using the integral of the distance from the center:

\[
E_{\rm average}\leq
L\frac{\sum_i\int_{a_i}^{b_i}|t-c|\,dt}{\sum_i(b_i-a_i)},\qquad
E_{\rm timing}\leq L\max(|d_{\min}|,|d_{\max}|).
\]

This deliberately conservative central bound replaces hundreds of receiver
factorizations; it does not pretend that a central value is an exact average.
The primitive \(x|x|/2\) evaluates the integral exactly in real arithmetic.
Qualify this change with independent constant, linear, tent and gapped histories
before launch. Preserve complete packets even when the unknown offset moves
their physical support across a nominal one-second boundary.

For measured continuous magnitude, retain the same corrected-increment and
direction-cone bounds. Evaluate gain/offset boxes ±1%/±0.05 m/s² and
±15%/±0.25 m/s². Also test **one fixed zero gain/offset correction for the
entire recording**, not separately chosen parameters in each group.

If the zero point is not excluded in every supported group, report that precise
necessary-constraint result. Other uncertainty dependencies are still relaxed:
it does not establish one jointly feasible receiver trajectory, gravity/latency,
orientation or full gyro-free reconstruction. A disjoint group rejects that
fixed point under these assumptions; it is not automatically an optimized
candidate rejection. Every scientific decision remains abstain.

## Finite execution and provenance

- At most 840 inventoried packet groups across the same two recordings.
- At most 3,360 charged identities: group × two clocks × two receiver-error boxes.
- One receiver operator and three candidate force boxes per identity: maximum
  3,360 operators, 10,080 force boxes and 30,240 scalar calibration comparisons.
- Zero optimizer starts, native integrations, original-file reads or downloads.
- One worker, four numerical threads, 30-minute overall wall ceiling; no retries.

Verify the preceding receipt, extraction artifact/cache hashes, frozen environment
and all source snapshots. Snapshot the reused caches and metadata as study inputs.
Charge each identity immutably before calculation. Interrupted identities remain
charged and cannot be retried. Check the deadline before each identity and use a
terminal deadline exception that ordinary calculation failure handling cannot
swallow. Completed or terminal work cannot restart or donate unused allowance.

Save group metadata, covered durations, receiver estimates/error boxes, per-model
measured/predicted bounds and every failure. Publish a CSV and shared-zero-point
summary per recording/clock/receiver-error/candidate. Relate findings to the saved
complete-observation dispositions, with discarded support explicit. This study
does not calibrate a likelihood or authorize corpus-wide refitting.

[Snapshot assumptions](../ilvis0-channel-envelopes-20261019/PLAN.md) ·
[Snapshot outcome](../ilvis0-channel-envelopes-20261019/INTERPRETATION.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
