# Common-acceleration native qualification

Freeze the same **24 byte-identical generated inputs** as the preceding native
qualifications: all three candidates, both processing cases and tangent,
packet-boundary, broad-region and independently specified stationary-pose
families. Keep their original 27 physical bounds and the unchanged native engine.

The candidate separates a constant reference acceleration and tracks relative
left navigation/right body rotations. It must retain all 27 physical plus 15
bounded common-error columns. The nine acceleration columns supplement the
previous six; neither block may be omitted. They represent shared mathematical
remainders, not new physical calibration choices at each epoch.

Use the same acceptance limits: native/independent-pose centers within
1 micrometre; all 162 physical tangent-column comparisons within
20 micrometres per normalized parameter at the fixed 0.002 step; known probe
residuals within the factored remainder plus 10 micrometres. Actual normalized
common vectors must lie within 1+1e-11 of their unit boxes. Save every native
value/Jacobian, reference definition, coefficient block and factored probe.
Local radial constant-acceleration, nonzero-lever and relative-rotation controls
must pass first. No relaxed test limits or smaller physical domain follows.

Limits: **78 native evaluations / 19,632 native packet visits**, **348 bound
evaluations / 7,536 reserved bound packet steps**, one worker with four numerical
threads and a separately frozen **300-second cooperative ceiling**. Tangent
identities reserve one native call and 55 bounds; other families reserve four
native calls and one bound. Charge/reserve before operations; no retries,
expansions, process signals, original-file reads, observed fits or protected ESA
outcome evaluation.

Passing qualifies only this finite native component. A source-bound joint
42-coordinate interface and a separate matched usefulness comparison must
follow. Recording-scale usefulness, whole-program numerical treatment and
observational coverage remain additional gates. All scientific outputs abstain.

[Derivation](../ilvis0-reference-acceleration/NATIVE_PLAN.md) ·
[Completed acceleration component](../ilvis0-reference-acceleration-controls/INTERPRETATION.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
