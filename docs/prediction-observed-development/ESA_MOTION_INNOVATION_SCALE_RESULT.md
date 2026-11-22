# A motion-dependent scale improves some forecasts' error scores

On the eight matched windows from ESA development flight 187, scaling
forecast uncertainty as the aircraft turned improved the held-out
joint log score in **six of eight windows**. It put **one of eight**
inside the original error reference, the same count as the original
covariance. The two inertial error descriptions gave the same results
to the displayed precision.

| Covariance rule | Total held-out negative log score | Windows inside the reference |
| --- | ---: | ---: |
| Original covariance | −9,562 | 1/8 |
| Fitted constant native scale | −9,562 | 1/8 |
| Fitted motion-dependent native scale | −10,143 | 1/8 |

Lower negative log scores indicate a better fit of the proposed error
distribution. Mean squared standardized error has a reference value
of one. In the hardest turn it fell from **3.34 to 1.33**, still above
the reference interval. In steady window 21856 it rose from **0.62 to
4.59**. The covariance changed how the errors were scored. The actual
forecast positions stayed fixed.

The scale selections used only the other three turn and steady pairs.
All four chose the same motion coefficient on the grid, while the
estimated quiet multiplier ranged from 0.135 to 0.368. The fitted
constant scale always reproduced the original rule. The results give
development evidence for a motion-linked variance term and show that
the tested term is insufficient for calibration. Every window comes
from one flight and has been used in earlier diagnostics.

All eight tasks completed in 26 seconds. Eight focused tests passed.
No trajectory fits or reserved flights were used.

[Frozen method](ESA_MOTION_INNOVATION_SCALE_PLAN.md) ·
[All scale and forecast-error scores](esa-motion-innovation-scale-result.json) ·
[Execution receipts](esa-motion-innovation-scale-evidence/README.md) ·
[Reproduction bundle](esa-motion-innovation-scale-evidence/bundle.zip)
