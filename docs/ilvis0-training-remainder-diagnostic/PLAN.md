# Recheck the last training allowance on a smaller domain

The saved endpoint audit identifies training-interval allowances as a substantial
part of the remaining prediction width. This diagnostic checks whether the
existing, qualified propagation method can reduce those allowances when given
the smaller physical domain already established by necessary constraints.

Use the six generated candidate/processing groups, always original yaw sector
4 and mounting child 0. These indices are fixed equally for all groups and are
not selected by generated truth or favorable bounds. Reuse the 1,600-packet
inputs, original reference, calibration bounds and last training epoch. The
entire child domain must remain inside the original reference domain.

Recompute one unconditioned propagation bound per group. Compare its center
with the saved native center to within 1 micrometre. Preserve all 51 augmented
coefficients exactly; otherwise report failure. Compare the recomputed interval
half-width, including the original 1 mm generated observation allowance and
saved arithmetic allowance, with the original training half-width. Report wider
or unchanged bounds as well as improvements. No training constraint is replaced,
no future prediction is made and no model is fitted.

Finite allowance: **six identities, six reference setups, six propagation bounds
and 19,200 reserved bound packet-steps** (two passes over 1,600 packets per bound).
Each bound has a cooperative 120-second ceiling; the overall ceiling is 600
seconds. Four workers use one numerical thread each. No native integrations,
LP proposals, support calculations, original-aircraft reads or optimizer starts.
No retries, expansion or process signals. Charge before each bound.

Passing the center/source/coefficient checks qualifies this comparison only.
Any later tightening of training constraints must separately preserve all old
constraints, complete coverage and independent endpoint audits. This diagnostic
does not qualify aircraft prediction or observation-error coverage.

[Saved endpoint audit](../ilvis0-coupled-subdivision/ENDPOINT_DIAGNOSIS.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
