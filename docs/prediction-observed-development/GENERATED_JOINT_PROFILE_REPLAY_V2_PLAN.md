# Generated joint-profile replay: bounded-point correction

Use the same sealed `straight-level` generated case, saved three fitted
calibrations, fixed receiver law, one task and one numerical thread as the
[first replay](GENERATED_JOINT_PROFILE_REPLAY_PLAN.md). The first task failed
after all three exact source forecast replays because the native decoder
rejected a profiled normalized point. Preserve that terminal failure.

This v2 task has no new fit starts. Save each candidate's complete bounded
linear profile and raw correction before native evaluation. The native point
must be within `5e-13` of every normalized bound. Only a smaller floating
overshoot may be projected to the exact existing boundary. Record the maximum
coordinate adjustment and recompute the linear profile cost at the applied
point; reject any material cost change. Reject larger infeasibility without
adjusting bounds or reoptimizing. Compare the applied tangent path to the
native nonlinear path and retain all 26 nuisance columns.

Freeze source/environment hashes, one-hour wall, one worker/thread, and the
same finite native-call and packet limits under a fresh study ID. Qualify the
source gate, point projection and task recovery before launch. No observed or
protected flights are read. This is development compatibility diagnosis, not
held-out prediction, calibrated coverage or a scientific detection.
