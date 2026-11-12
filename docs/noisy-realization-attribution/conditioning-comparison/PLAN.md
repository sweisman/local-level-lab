# Compare noise scales on the same information footing

The published linear benchmark reports 33.77 m later horizontal error scale
**after conditioning on 800 earlier receiver observations**. The completed
same-noise oracle does not update its forecast with those observations. This
finite generated-data calculation will report both covariance scales from
one unchanged error operator, making the comparison explicit.

Use the preselected rotating-globe, zero-removal case at 55° latitude, with
the same 1,200-second fast/climbing trajectory, 300 Hz ideal increments,
recorded-increment noise law and 1,200 receiver queries. Reuse the benchmark's
published noise settings and receiver-error policy. Compute the later 400
epochs' horizontal and height second moments both from the **unconditional**
state and from the state conditioned on the first 800 receiver epochs. Neither
calculation draws a noise path, estimates calibration, fits a model or reads an
aircraft recording.

The operator construction permits at most 361,200 native steps and one bridge
build. Use one worker with one numerical thread, a one-hour cooperative ceiling
and a separately qualified task-level recovery policy. Freeze source, inputs,
environment and the single task before launch. Save both variance curves,
their physical RMS scales, exact charge record and source hashes. Independent
tests must compare a small operator against dense covariance and verify that
conditioning reduces or leaves unchanged the uncertainty. Audit and publish
from saved results without recomputing the operator.

This is an error-scale diagnostic. A realized noisy forecast need not equal
either expected scale. No statistical tail claim, aircraft error calibration
or Earth-model decision follows from it.
