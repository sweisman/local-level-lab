# Measure receiver-specific changes to the saved shape score

Use the archived satellite omission geometry, the 518 matched carrier
intervals from the three receivers and the unchanged shape-score operator.
Recover each position-only pseudoinverse from the saved omission correction
and its withheld residual. Invert the pseudoinverse to recover the range
geometry centered across satellites. Check the recovered matrix against
the saved gain before using it, then center again on the common subset.

For each integer-second interval, use the same satellites for all three
receiver comparisons and both half-second geometry choices. Require at
least five satellites and the existing condition limit of 100. Project
the saved one-second differences into small position corrections using
the opening and closing half-step geometries separately. Check that the
three pair corrections close algebraically. Accumulate from the same
earlier anchor and evaluate the frozen score. Report separate corrections
from Septentrio and NovAtel relative to AIR1, plus the pairwise differences.
Leave the clock-step interval uncorrected for all pairs and report the
score sensitivity per metre of unmeasured displacement at that interval.

Run one task on one numerical thread, with 519 charged interval checks and
a 60-second cooperative limit. Preserve the per-interval supports and
corrections. This linearized comparison quantifies receiver-specific
effects on fixed forecasts. It supplies no absolute receiver error bound,
new trajectory or inertial fit, protected flight read, or scientific decision.
