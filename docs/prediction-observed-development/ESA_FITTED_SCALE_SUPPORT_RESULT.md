# Flight calibration absorbs most of the steady error signal

In the saved ESA 400-report training interval, adjustments to the flight
path can account for more than 99.5% of the steady-acceleration error
pattern. The brief maneuver pattern leaves more room to estimate its
scale, but the available information is still limited. The three Earth
models give nearly the same result on this one flight.

| Error pattern | Squared loading left after calibration | Information at 0.0001 m/s² | Information at 0.001 m/s² |
| --- | ---: | ---: | ---: |
| Steady acceleration | 0.415–0.424% | 0.00024–0.00025 | 0.243–0.245 |
| Short-lived maneuver response | 14.45–14.52% | 0.00097–0.00103 | 1.000–1.013 |

The percentages describe the remaining pattern in receiver coordinates
weighted by the original error model. They are not percentages of observed
error explained. The last two columns are local information for the log
of the variance at two reference error sizes. They hold the original
covariance scale fixed and examine one additional term at a time, so a
joint estimate can have still less information. The reference sizes are
test inputs, not measured aircraft errors.

The archive has 27 receiver intervals above the motion threshold on
this part of the flight. Each model's mean design has rank 27 at both
declared tolerances. The replay verified all three archived training
derivatives against their saved fits. It ran no new fits.

**What this changes.** A quiet interval can help check steady drift,
but its flight calibration may absorb the same pattern. Simply adding
windows from this flight cannot substitute for constraints on calibration
or evidence from independent flights. Before estimating aircraft error
ranges, test how much information can survive independently justified
shared or bounded calibration. The projection here allows unrestricted
local calibration changes and gives no answer for the bounded nonlinear
fit.

[Study plan](ESA_FITTED_SCALE_SUPPORT_PLAN.md) ·
[Frozen inputs](esa-fitted-scale-support-freeze.json) ·
[Detailed results](esa-fitted-scale-support-result.json)
