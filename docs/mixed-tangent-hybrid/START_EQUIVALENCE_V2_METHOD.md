# Cost and start checks for a future faster tangent method

The completed two-start study remains failed under its frozen rule. A
separate versioned comparator now handles training costs near zero and
requires forecast stability **within** each method's near-minimum starts as
well as across methods. It preserves the original checks that every fit pass,
the input and forecast grid match, same-start costs agree, and a changed
primary start be near-minimal under both methods.

Its cost rule is

`|cost A − cost B| ≤ absolute floor + relative tolerance × max(cost A, cost B)`.

The proposed absolute floor for this **near-zero generated protocol** is
the already declared near-zero stopping ceiling, `1e-8` sum-of-squares units
from `ilvis0_near_zero.POLICY`. The relative tolerance remains `1e-8`, and
the forecast separation limit remains `0.01 m`. This floor was part of the
solver's existing policy before the first two-start result; it was not chosen
from that result's cost gaps. The comparator rejects an invalid floor and a
case where two same-method starts differ by more than the forecast limit even
though each is close to the other method.

Applying this revised rule to already sealed fits is **retrospective
diagnosis only**. It cannot turn the failed study into a qualification. A new
prospectively frozen generated scenario and then a separately selected
development recording must pass before the faster method can replace the
established wide calculation. The absolute floor applies only where that
same near-zero stopping policy governs the objective; it is not transferred
to an observed-aircraft cost automatically.

The [saved-result diagnostic](start-equivalence-v2-retrospective.json) verified
the sealed study and passes all six groups under this revised rule. The
original frozen result remains **2/6**, and the retrospective 6/6 result does
not authorize method substitution.

The original adapter fixed a 120-second route. A separate
[prospectively frozen 180-second study](START_EQUIVALENCE_V2_RESULT.md) now
passes all six settings under the revised rule. It uses newly generated
training and forecast times, preserves the old failed study, and still does
not authorize observed-aircraft substitution. That requires a separate
development comparison with a justified observed-objective tolerance.
