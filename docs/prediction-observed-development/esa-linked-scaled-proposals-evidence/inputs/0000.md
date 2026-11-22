# Rescale the calibration searches within the surviving child ranges

Use the eleven surviving children from the [child certificate study](ESA_LINKED_CHILD_CERTIFICATES_RESULT.md).
Its approximate score optimizer reported convergence on none of the 15
children. Keep the original physical box, earlier loss, score, dimensions,
and static constraints. Express each variable in units of its available
range within the child before proposing the earlier-loss and forecast
score directions. Transform the residual, design, bounds, objective and
constraint right-hand sides together. Keep a fixed coordinate fixed.

Use the same optimizer and 120 iterations per search. Verify on generated
matrices that the normalized problem preserves the squared residual,
original bounds, linear constraints and score differences. Check the new
directions and weights with the existing exact certificate on the original
physical box. A search error or a weaker certificate leaves the existing
bound in force. Recheck all saved feasible points. Combine the results
with the unchanged cover using the original 25.41-unit score gap.

Use eleven identities and at most 44 charged calculations, with two
one-thread workers and a 120-second cooperative limit. Use zero new
trajectory fits, native calls, later GPS positions or reserved-flight
reads. Report solver statuses separately from certified dispositions.
Keep the full dynamic remainder and aircraft uncertainty gates separate.
