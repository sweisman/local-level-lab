# The Galileo limit adds little to the broader GPS path bound

The previously tested northward displacement worsens the [Galileo range fit](ESA_GALILEO_NORTH_WITNESS_RESULT.md). Across the broader set of possible path errors, the joint bound found that the existing GPS, anchor and motion limits do most of the work. The result uses an illustrative **8 mm RMS Galileo range-error cap**. The observed Galileo residual on the final GPS reference path was **6.00 mm RMS** across 1,067 matched ranges.

| GPS satellite set | Prior continuous GPS-only upper bound | Joint upper bound | Can the published bound exclude a full score-gap path? |
| --- | ---: | ---: | --- |
| Full set | 50.22% | 50.18% | Yes, under the example caps |
| 0° starting tilt screen | 100.59% | 98.33% | Yes, under the example caps |
| 5° starting tilt screen | 102.46% | 101.17% | Undetermined |
| 10° starting tilt screen | 111.40% | 109.03% | Undetermined |

Changing the Galileo cap from 8 mm to 1 m changes these upper bounds by less than 0.000003 percentage points when the saved proof coefficients are held fixed. The slight improvements in the table do not establish that Galileo supplies an effective error limit. The previous [GPS accuracy requirements replay](ESA_CARRIER_ERROR_REQUIREMENTS_RESULT.md) also put the 0° screen below the gap, at 99.25%.

The analysis averages the two same-antenna Galileo receivers and holds transmit states and modeled neutral delay fixed for the path perturbation. The GPS and Galileo limits, position anchors and aircraft motion limits are still assumptions. Two screened cases remain open even under those assumptions. No shape or field decision follows from this calculation.

All 365 planned checks completed in one task. No aircraft model was refitted, no extra data were downloaded, and no reserved flight was opened. [Frozen plan](ESA_GALILEO_JOINT_BOUND_PLAN.md) · [Preflight record](ESA_GALILEO_JOINT_BOUND_PREFLIGHT.md) · [Coefficients, observations and completion receipt](esa-galileo-joint-bound-result.json)
