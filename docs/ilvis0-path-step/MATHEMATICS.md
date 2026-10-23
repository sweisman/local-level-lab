# Midpoint-step implementation

Each scalar contains outward intervals for its value and its first three actual
path derivatives. Products use the binomial form of the Leibniz rule. Divisions,
square roots and trigonometric functions use the separately checked compiled
arithmetic. All operations reject unsupported or nonfinite results.

The motion step follows the rational reference: initial geographic rates,
midpoint coordinates, a trial local solve, revised rates from the average
velocity, a second local solve, then the coordinate update. Each local solve
uses midpoint attitude for specific force, a full attitude update, and the
three-dimensional Cayley-form velocity solve. Upstream removal subtracts the
same specified geographic field under every physical candidate.

Small rotations retain the native Rodrigues polynomial. Larger rotations use
the trigonometric expression. This component rejects a domain spanning the
switch; it does not silently assume smoothness or substitute an exact rotation
for the small-angle polynomial.

Six tests compare every state component through third order with the rational
reference using 192-bit outward rounding. Additional tests cover a known gain
response, stable rotation branches, unsupported inputs and the compiled source
closure. The reference remains a separate Python implementation. These finite
checks are software qualification, not an exhaustive whole-program proof.
