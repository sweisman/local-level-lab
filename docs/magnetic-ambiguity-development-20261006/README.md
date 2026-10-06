# Wind or movement of the IMU mount?

An **IMU (inertial measurement unit)** measures turning and acceleration. Its magnetic compass
helps detect movement of its mount. Changing wind can produce a similar magnetic change, so a
watchdog flag is evidence of ambiguity rather than proof of mount movement.

The optional research candidate retains most flagged measurements and allows an unknown yaw
offset and slow yaw drift at flagged intervals. Yaw is turning about the local vertical. Each
mount epoch has its own interval parameters. The first bin at a flagged boundary is excluded
because an abrupt change could contain a gyro impulse that this model cannot reconstruct.
The original recording is preserved.

The analyzer then reruns the original exclusion method on the same recording. That path has
its own preprocessing, forward-axis estimate, magnetic selection check and scientific gates.
Both paths must be informative, give identical endpoint decisions and have estimates within
one reported standard deviation. Each model pair is checked separately. Missing control data,
prior dependence, parameter boundaries, insufficient bootstrap, integrity failures or disagreement
cause abstention. A global three-model failure does not automatically discard agreed pair evidence.

The default exclusion path is preserved. The new comparison is development-only, has no
empirical calibration and cannot apply empirical decision policies. It cannot rescue a recording
whose exclusion path has no usable evidence. Passing software checks does not demonstrate improved
power or a safe error rate; matched campaigns remain necessary.

`mount-yaw-1` uses provisional 3-degree offset and 3-degree/hour rate priors, coefficient bounds
of ±15 degrees and ±15 degrees/hour, and a 1% boundary abstention margin. The design calculation
checks zero and individual ±3-sigma offset/rate states as well as its other nuisance states.
This finite grid does not cover every combination, nonlinear creep or unknown boundary motion.
The magnetometer supplies boundaries, not fitted yaw angles or gyro corrections.

Use `magnetic_ambiguity='model_and_compare'` in analysis options, or
`--magnetic-ambiguity model_and_compare` in `analysis/tests/research.py`, together with
envelope design and direct pair profiles. Requested bootstrap requires nonlinear refits.
The analyzer supplies watchdog segment IDs; users cannot override these boundaries there.
Diagnostics retain the mount-yaw curve and a separate original-path result.

**119 focused checks passed in 15.90 seconds**, including passive rotations constructed with
SciPy, zero and positive/negative 3-degree/hour controls, analytic derivatives, bounded/nested
profiles, malformed decisions, independent pair eligibility, encoded recording retention and
original-path reruns. These are controlled fixtures, not a flight campaign. The previously
committed source passed all 336 Python checks; the full suite has not been rerun for this extension.

No campaign, optimizer search, calibration or validation was run. Current source changes make
earlier prospective manifests stale; refreeze them before an authorized pilot. Operational
domain enforcement and sharded execution were subsequently implemented. The refreshed
[airline pilot](../airline-pilot-preparation-20261006/README.md) remains unrun and needs a new
budget; true mount-slip controls still need their own matched stage.
