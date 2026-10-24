# Observed prediction with height-dependent gravity

## Prerequisites and question

This development comparison may be prepared only after all 24
[long training/forecast controls](../esa-height-training-controls/README.md)
qualify and their saved-data audit is published. A verified report without full
qualification is insufficient. The [known-correction gravity controls](../esa-gravity-controls/README.md)
and unchanged fitting/scoring components must also remain source-bound.

Does the declared height-dependent gravity law improve the previously selected
ESA recording-187 forecast without changing observations, calibration bounds,
starts, weights or accuracy limits? The [first observed pilot](../esa-development-pilot/README.md)
remains intact, including every failed fit and inaccurate forecast.

## Fixed data and single physical change

Reuse the exact prepared twenty-minute interval: 360,028 constructed increments,
800 earlier receiver positions for training and 400 later positions for scoring.
Copy and verify the original prepared artifacts and their hashes. Recheck
explicit development membership before execution. Read no original aircraft file
and no protected confirmation observation. Do not choose a quieter interval.

The single change is the same declared height-gravity law for all three candidates:

`g(h) = g_anchor × ((6,371,000 + h_anchor) / (6,371,000 + h))²`.

Bind `h_anchor` to the first **training receiver** height. Keep the existing
force-based initialization and bounded constant gravity adjustment for
`g_anchor`. Evaluate `h` from predicted midpoint state, never later receiver
heights. Add no drift, gravity-gradient or other free parameter. Preserve every
existing nuisance column.

Reuse the shared observed calculation and its common receiver-coordinate scoring.
A thin library adapter records the gravity variant and earlier-only anchor;
it must not introduce a separate optimizer, score or forecast reset.

## Separate finite allowance

Keep the original 24 identities: three candidates × two processing cases × two
working receiver-error policies × two starts. The starts remain zero and the
alternating ±0.001 vector. Retain the near-zero stopping method and at most
200 training evaluations plus one full forecast per identity.

The new allowance is **4,824 native calls**, **931,458,086,400 packet/query
visits**, four workers using one numerical thread each, and a cooperative
eight-hour ceiling. Starts and evaluations are charged before execution. There
are no retries and no reuse of unused allowance from the first observed pilot.
Freeze new source, environment, inputs, policy and parent-report hashes before launch.

## Comparison and reporting

Select a primary using converged training cost alone. If its forecast fails,
retain the failure; do not replace it based on later accuracy. Keep both starts
and every incomplete setting visible. Compare the better globe forecast with
the specified disc first. Withhold field ranking until the required shape
comparison completes and the preferred model passes physical accuracy.

The original physical screens apply in both sections: horizontal RMS ≤10 m,
height RMS ≤30 m, maximum horizontal error ≤50 m and maximum absolute height
error ≤150 m. Lower error alone is not an adequate reconstruction. Working
covariances remain assumptions, not calibrated observation errors.

Publish the saved errors, convergence labels, input/anchor bindings and all
charges without refitting or propagation. Compare descriptively with the first
pilot under matched candidate, processing, policy and start. Improvement would
not by itself identify the cause of the earlier error or establish significance.

This remains one development recording. All seven confirmation groups, the
original NASA findings, field-cause interpretation and solar/sidereal questions
remain unchanged.

[Training-only gate](../esa-height-training-controls/README.md) ·
[First pilot](../esa-development-pilot/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
