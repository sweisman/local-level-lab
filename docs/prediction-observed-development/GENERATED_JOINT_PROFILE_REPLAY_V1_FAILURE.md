# Generated joint-profile replay: first technical result

The one-case study `data/generated-joint-profile-replay-v1-20261117` closed
terminally after 79 seconds. Its single task failed with
`ValueError: invalid conditional bound coordinates`. All three regenerated
forecasts and training error bindings had already matched the sealed source;
`all-input-replays-passed.json` was saved before the later generated path was
opened. The failure occurred while trying the first candidate's profiled
calibration in the native forecast. No model comparison was reported.

The frozen task charged 504,933 native calls and 1,129,863,330 packet visits
as a prepaid finite block; 106,662 calls and 12,958,659 visits were attempted.
Its result and source freeze remain unchanged. The bounded linear solver may
return a value that exceeds a normalized boundary through floating-point
addition, but the failed task did not save its profile before the native call.
The exact size of this case's boundary discrepancy is therefore unknown.

A separate v2 study will save each linear profile before native evaluation.
It will project to the exact feasible boundary only when the overshoot is at
most `5e-13` in normalized coordinates, record the adjustment and its effect
on profile cost, and reject larger discrepancies. It will reuse the same
sealed source case and fitted parameters without refitting. This is numerical
feasibility handling, not a change to the physical calibration bounds.
