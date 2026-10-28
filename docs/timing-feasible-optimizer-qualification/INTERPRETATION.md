# The revised optimizer passes the analytical qualification

**All 36 known-answer fits and eight direct checks pass.** All nine groups of
prescribed starting points agree. The new run finishes in 27.8 seconds on one
thread, using 1,046 analytical evaluations and 927 linear operations after
148 source-bound software checks.

These mathematical problems test the complete fitting and stopping procedure,
including active bounds, weak or redundant directions, timing corners and
physical-change checks. Their reference answers are specified independently of
the optimizer. Correct rejection of the deliberately bad cases is required.
The revision uses feasible initialization for its bounded linear calculations;
the original parameter bounds and acceptance limits remain in force.

This is software qualification, not a new aircraft result. No native trajectory
integrator, generated IMU history, original observation or protected data was
used. Earlier failed studies remain unchanged.

The next gate is a new finite native trial, including the newly exposed
calibration failure and earlier regression controls. Its inputs, sources,
environment and maximum work must be frozen separately. The closed calibration
still supplies no threshold, so independent validation cannot start.

[Verified report](README.md) · [Results CSV](results.csv) ·
[Starting-point comparisons](pairs.csv) · [Frozen plan](PLAN.md) ·
[Next analyses](../NEXT_STEPS.md).
