# Test one axis-specific gain and offset correction across each recording

Use the same two recordings, 991 force windows, two packet clocks and
earlier/later split. Keep both GPS paths together and test the saved
quadratic and fourth-degree force enclosures separately. Use no gyro
observations or fused attitude. Hold the gravity adjustment at zero.

Give each accelerometer axis a constant gain and offset. Reuse the earlier
[calibration boxes](../ilvis0-channel-history-v2-20261019/PLAN.md). The narrow
box allows ±1% gain and ±0.05 m/s² offset. The wide box allows ±15% gain and
±0.25 m/s² offset. A training-only linear program proposes one correction by
minimizing the maximum interval gap using the magnitude derivative at zero
correction. Save the proposal, then apply it to the original signed counts
under the exact nonlinear norm and half-count bounds. Verify the earlier
and later intervals at that one correction.

The linear program gives a proposal. Its objective does not bound the
nonlinear optimum, and an exact evaluation at one proposed point cannot
exclude other calibrations. Packet averages also leave the within-packet
direction limit unresolved. Preserve every numerical failure and any
calibration coordinates at their declared limits.

Use 32 tasks, each allowed one linear program with at most 1,000 iterations
and two seconds. Use two single-thread workers and a cooperative three-minute
wall limit. Use zero navigation fits. Save the charge before each proposal
and keep the later receiver cases out of the proposal.
