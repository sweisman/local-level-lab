# What remains in the development plan

The main implementation work from the review is present. The remaining task is demonstrating
that useful flight geometry survives realistic instrument and aircraft uncertainties, then
calibrating and independently validating the resulting decisions. Implemented software and
successful numerical fits do not establish that the physical models can be distinguished.

| Review item | Present in the software | What still needs evidence |
|---|---|---|
| Nuisance envelope | Design checks vary crab, wind, forward angle and mount epochs across model anchors. | Show that a selected geometry survives the declared envelope and complete preprocessing. The finite grid is not a guarantee over every nuisance trajectory. |
| Real airline trajectories | Replay input and five prepared windows exist; two supplied tracks were unsuitable. Matched pilot prefixes have run. | A useful route/window and IMU-turn schedule. The pilots so far yield no eligible contrasts; the full proposed comparisons remain unfinished. |
| Turns away from maneuvers | Buffered aircraft-motion checks guard planned IMU turns. | A schedule that passes these checks and preserves model separation on an actual route. |
| Physical wind and airspeed | An optional north/east wind and true-airspeed candidate is integrated. | Justify its assumptions and conditional speed information, then compare it with the broader wind candidate. Choosing the more restrictive candidate merely because it passes is insufficient. |
| Magnetic ambiguity | Optional piecewise mount-yaw modeling retains ambiguous data and requires agreement with the exclusion path. | Independent calibration of both paths and evidence for genuine mount movement versus aircraft crab. The default remains exclusion. |
| Combined adversaries | Composable wind and mixed sensor-bias scenarios are implemented and used in pilot work. | Matched comparisons over the final nuisance domain, including relevant correlated-noise and thermal combinations. |
| Pairwise evidence | Direct pair-specific profiles, abstention, pooling and globe/disc preferences are implemented. | Fresh pairwise calibration, pooled-domain validation and a separate error budget for the composite globe/disc rule. Historical development preferences are uncalibrated. |
| Operational domain | Versioned observable domains bind primary/pairwise eligibility and threshold artifacts. | Select and validate a useful domain, with actual threshold files. Real-upload empirical decisions remain refused. |
| Parallel campaigns | Deterministic, journaled two-worker execution and checked merging are implemented and exercised. | A new bounded budget for further simulations and a final frozen scientific configuration. Each worker uses one numerical thread. |

Recent processing work also addresses nuisance-rank scaling, forward-reference noise/motion
handling and finite-run course unwrapping across gaps. Actual forward-reference uncertainty
and its statistical coverage still need evidence; software fixtures do not establish it.

The immediate order is:

1. Continue inexpensive route/window/turn screening under the unchanged nuisance space.
   Evaluate rotation and globe/disc questions separately. Seek an actual observed route,
   not only a counterfactual direction control.
2. For promising controls, review the finite envelope assumptions and obtain a separately
   bounded budget for complete-envelope evaluation and matched full-pipeline replay.
   Preserve every failure and abstention. Do not rerun spent attempts to improve acceptance.
3. Decode the supplied airborne IMU using a documented physical format, and qualify actual
   devices when available. These are separate evidence sources: the NASA instrument cannot
   establish consumer-device drift or accuracy.
4. Once a useful domain is demonstrated, freeze source, configuration, eligibility policy,
   observable domain and numerical environment. Preregister primary, pairwise, pooled and
   composite-shape error budgets where applicable.
5. Run fresh calibration, freeze its actual decision artifacts, then run independent
   validation and assess the simultaneous exact bounds. Production use follows a reviewed
   policy revision, not a development preference.

All previously authorized simulation attempts have been spent; no worker is being launched
by this continuation. Earlier calibration costs and prospective execution freezes are stale.
No usable fully validated protocol or empirical Earth-model result has yet been demonstrated.

## Latest inexpensive check

A fixed reversed traversal of the preserved 120-minute AUH–ORD path, with six IMU turns,
previously passed a nominal globe/disc design check under the physical wind candidate.
The bounded follow-up evaluated 30 states from the existing registered envelope in about
0.10 seconds. These include zero wind and some individual wind drifts, all three model
anchors for completed state groups, and forward-angle offsets of 0° and ±15°.
Both globe/disc retained fractions remained above the threshold in that subset: minima
0.403480 and 0.431011 against 0.312250. The evaluation cap stopped partway through the grid.
This found no counterexample; it did not complete or certify the envelope. Other wind
corners, airspeed levels, mount epochs and noise states remain unchecked here.

The broader wind candidate already fails the nominal check on this same reversed path.
The reversed traversal is not a measured eastbound flight, and no sensor synthesis, fitting,
bootstrap or calibrated decision was performed. Thus this remains a design clue, not a
protocol recommendation. The recorded states and input/helper hashes are preserved in
`direction-envelope-counterexample.json`, produced by
`analysis/tests/check_direction_counterexamples.py`.

The [airborne sample notes](airborne-sample-ilvis0/README.md) and
[format follow-up](FORMAT_FOLLOWUP.md) describe the separate real-data step.
