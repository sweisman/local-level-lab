# Bounds for changing calibration and orientation

The prediction work needs an error allowance that stays valid while calibration
and timing vary. This component carries a quantity and its first three
derivatives together, using exact rational intervals. It also bounds a
three-axis rotation without assuming the axes commute.

Six focused tests pass, including independent scalar trigonometric series,
an exact noncommuting rotation example and outward dyadic rounding. Together with packet derivatives and
piecewise error arithmetic, 29 tests pass. No aircraft fits or native trajectory
evaluations were used.

These are mathematical building blocks. They do not yet bound a complete
reconstructed flight or establish observational uncertainty. The next step is
to propagate them through the trajectory equations, account for packet-boundary
changes and check whether the resulting ranges are useful.

[Mathematics](MATHEMATICS.md) ·
[Remaining trajectory work](../ilvis0-calibration-path/NEXT_PLAN.md) ·
[Prediction requirements](../ilvis0-long-staged-feasibility-v2/V01_GATES.md)
