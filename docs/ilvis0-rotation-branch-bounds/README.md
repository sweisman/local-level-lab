# Bounding the rotation formula's switch

The native motion calculation uses a short polynomial for very small rotation
increments and a trigonometric formula for larger ones. A calibration range
can cross that switch. Treating the whole range as one smooth formula would
miss a small change between the two expressions.

A separate component now encloses both formulas and bounds that change through
third derivative order. Three checks pass against independent scalar polynomial
and trigonometric references. The small-angle result retains the native
polynomial rather than replacing it with an exactly orthogonal rotation.

This covers one local switch for a smooth supplied input path. It does not
cover incoming jumps, propagate changes through a whole flight, establish
clock-boundary completeness or bound native floating-point execution. It is
not installed in either running study.

[Mathematics](MATHEMATICS.md) ·
[Trajectory components](../ilvis0-path-motion/README.md) ·
[Prediction requirements](../ilvis0-long-staged-feasibility-v2/V01_GATES.md)
