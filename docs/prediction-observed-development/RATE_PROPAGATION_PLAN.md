# Fixed-parameter ESA rate-interpretation check

## Question and scope

On development recording 187 only, do the three plausible ways to integrate
the reported iMAR rates materially change the aircraft coordinates predicted
by the existing fixed globe-with-field fit? The interpretations are left hold,
right hold and the saved linear-point construction. This is a **sensitivity
diagnostic**, not a choice of instrument convention or an Earth-model test.

Use the sealed continuation's hash-verified IMU interval, first 800 receiver
positions, fixed 26-parameter fit, 800/400 split, candidate model, clock,
calibration bounds and processing assumption. Recompute the original initial
state and gravity anchor once from the saved linear increments and earlier
receiver rows; hold both fixed for all three propagations. Change only the
constructed angular/velocity increments. Do not refit parameters or use the
400 later receiver positions to initialize, adjust or select a trajectory.

The baseline native forecast must reproduce the sealed forecast at its saved
parameters within a predeclared tight numerical tolerance before interpreting
the alternatives. Report each alternative's displacement from that baseline
through the earlier and later periods, and its absolute receiver error only
after the three trajectories are sealed. Retain horizontal and vertical
differences separately. Failure to reproduce the baseline is a technical
failure, not evidence for any sampling hypothesis.

## Qualification and finite work

First test the component construction and fixed-point runner on a short
known-answer generated interval. Verify unchanged point/initial state, exact
baseline reproduction, later-receiver isolation, source hashes and task-level
reboot recovery. Then freeze source and numerical environment for three task
identities, one per interpretation. Each task may make **one** 360,028-packet,
1,200-query native tangent call per start, at most two charged starts if the
first is interrupted; sealed results and completed failures are never retried.
Thus the ceiling is six native calls and 2,592,201,600 packet/query visits.
Use one worker and one numerical thread with a cooperative 45-minute initial
wall allowance. Record every charge before execution. A separate saved-only
report assembles the sealed outputs; it must not propagate or fit again.

Keep the seven reserved ESA confirmation groups unopened. Small integrated
component differences alone do not license a position-insensitivity claim;
this test answers that narrower position question directly at one saved point.
It cannot identify filtering, coning/sculling, true sampling phase or the
cause of the existing 40-metre training mismatch. If position sensitivity is
large, an independently justified convention and matched reoptimized fits
would be needed before an empirical decision.

[Saved component check](RATE_HYPOTHESIS_AUDIT.md) ·
[Existing development result](CONTINUATION_RESULT.md).
