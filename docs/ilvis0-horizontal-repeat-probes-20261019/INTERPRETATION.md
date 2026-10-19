# What the fixed-point checks explain

All **28 evaluations completed in 5.13 minutes**, with zero optimizer starts.
The six failed-pair endpoints and two passing controls reproduced their saved
residuals and derivatives exactly. The original fit and repeat labels remain.

## Timing and calibration move together

The two IMU21 zero-field globe endpoints differ by about 19 ms in timing. Under
both processing assumptions, their horizontal costs are approximately 5.56418
and 5.57307. Swapping only their time offsets increases cost to about 18.73 and
changes predicted horizontal positions by **4.43 m RMS**. Moving the complete
parameter vector halfway instead gives cost **5.56950**, with horizontal changes
of only about **4 mm** from either endpoint.

Timing therefore cannot be investigated independently of its compensating
calibration coordinates. The full midpoint is not an optimized profile point;
these checks alone do not establish separate minima or a timing-derivative error.
The saved affine corrections make micrometre-scale horizontal changes and do
not bridge the repeat disagreement.

## The flat fit has an unobserved vertical direction

Changing only gravity correction between the two unsubtracted flat endpoints
leaves the horizontal predictions and cost unchanged, while changing predicted
height by **668.6 m RMS**. In this flat formulation, that direction is invisible
to the horizontal objective. This is a concrete consequence of removing the
height constraint, not measured vertical motion of the aircraft.

The complete midpoint changes horizontal positions by about **0.66 mm RMS**
and height by **326.6 m RMS**. The full affine step from the repeat endpoint
increases actual cost despite a tiny predicted improvement; the original
1.21 mm north-axis repeat difference remains above its 1 mm limit. A midpoint
or favorable probe cannot replace an independently converged repeat.

## What follows

The completed [timing-path diagnostic](../ilvis0-horizontal-timing-path-20261019/DIAGNOSIS.md)
compares independent finite differences with the timing Jacobian and samples
the complete path between endpoints. Its 29 calls find no gross derivative
fault. It uses zero optimizer starts and changes no clocks or physical bounds.

The separate horizontal-only result remains **one complete globe preference
and one unresolved comparison**. Its unscored height errors can be enormous;
it establishes a horizontal score advantage, not adequate full-flight paths
or gyro-only evidence. The original full-position findings remain
**53 globe / zero flat / zero unresolved**.

[All point results](README.md) · [Two-recording results and limitations](../ilvis0-horizontal-repeat-audit-20261019/INTERPRETATION.md).
