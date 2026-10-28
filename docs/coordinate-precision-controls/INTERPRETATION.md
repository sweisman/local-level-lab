# Coordinate compensation passes the small known-answer controls

**The new calculation preserves tiny changes in all six coordinate controls.**
The original arithmetic passed three; moving only the longitude origin passed
four. Compensation passes all six under the same relative comparison tolerance.

| Arithmetic | North controls | East controls | Height controls |
|---|---:|---:|---:|
| Original | 1/2 | 1/2 | 1/2 |
| Inward timing and relative longitude | 1/2 | 2/2 | 1/2 |
| Inward timing and compensated coordinates | 2/2 | 2/2 | 2/2 |

Each pair uses the same simple motion at small and large coordinate origins.
Large origins make it harder to retain small additions. The original calculation
loses the smallest north/east changes entirely in these fixtures and has about
1% relative error in the large-height case. Compensation keeps the rounding
remainder rather than discarding it.

The largest compensated difference error is about **0.000000003 relative to
the independent reference**, below the fixed 0.0000001 comparison tolerance.
That figure describes a mathematical software check, not measured gyro accuracy.

## What was tested

The reference differentiates the discrete midpoint impulse sum without using
the native derivative code or a shared truth generator. The fixtures deliberately
use large coordinate origins; the one-million-metre height is an arithmetic
stress case, not an aircraft observation. Gravity is constant in these origin
tests so translating height does not change their physical motion.

The 46 source-bound software checks also cover all three physical candidates,
both processing cases, every nuisance column, height-dependent gravity, partial
packets, initial-position corrections, lever arms, longitude wrapping and
forecasts without later receiver positions. The earlier inward timing convention
is retained. The shared native loader avoids copying the loader into each study.

The frozen study completes all **18 tasks in 7.13 seconds**, using one numerical
thread, three charged compiler builds, 126 native evaluations and 16,380
conservatively counted packet-query visits. Baseline precision failures remain
visible in the CSV. Task completion is separate from passing a precision check.

## What remains

These short controls qualify the arithmetic for a further diagnostic, not for
new scientific conclusions. They do not establish accuracy over an entire
recording or resolve the previously failed fits.

The next finite comparison should test the same four exposed saved points,
retain every derivative column, and repeat the original stopping check as a
diagnostic without changing any fit label. It must verify the original input
arrays, error operator, environment and baseline cost first. No fresh calibration
campaign follows automatically.

No nonlinear fits, new noise examples, aircraft reads or protected observations
were used. The original 53-stretch findings and failed calibration labels remain
unchanged.

[Verified report](README.md) · [Results CSV](results.csv) · [Frozen plan](PLAN.md) ·
[Previous four-point comparison](../saved-point-timing-arithmetic/INTERPRETATION.md) ·
[Next analyses](../NEXT_STEPS.md).
