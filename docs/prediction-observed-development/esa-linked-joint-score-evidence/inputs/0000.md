# Bound the signed forecast score with the training constraints kept together

The [coordinate check](ESA_LINKED_COORDINATE_RESULT.md) narrowed all eleven
surviving calibration ranges and left a 53.10-unit combined bound against a
25.41-unit gap. Use the same ranges, saved feasible points, earlier loss cap
of 0.01 and zero earlier unshared error. Keep every prior exclusion.

Use the certified contracted physical box with all 33 remaining shared or
lifted coordinates. Keep the 270 static inequalities and the five checked
earlier-loss rows from each coordinate projection. Put the signed forecast
score on this full 60-column domain. Enclose its coefficient error over the
whole box and add that allowance to the certified upper bound.

For each range, propose a linear-program maximizer and nonnegative dual
weights. Check those weights with exact arithmetic and a separate evaluator.
If the proposed point exceeds the earlier loss radius, form one more
necessary row from its training residual and repeat. Limit each range to
eight proposals and seven added rows. This uses optimizer output only to
suggest directions and weights. An unavailable proposal or inconsistent
certificate cannot lower the previous bound or exclude a range.

Retain the smallest checked bound per range and verify every previous
feasible point against it. Recombine the full cover with the unchanged
original bounds. Use eleven tasks and two one-thread workers with a
180-second cooperative limit. Reserve every proposal, exact check and
training row in advance. No model refit, raw recording read, later GPS
position read or reserved flight enters this check. This remains a static
bound with the original integration remainder and aircraft uncertainty open.
