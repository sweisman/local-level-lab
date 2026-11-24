# Screening low satellites keeps continuous coverage but weakens the score geometry

All three antenna-plane screens retained at least four satellites in
every half-second interval of the two-minute ESA comparison. The retained
satellites put less independent constraint on position. With exact
anchors and the earlier acceleration allowance, the screen cut the
range error allowance from **1.97 mm RMS** to **0.16–0.29 mm RMS**.

| Maximum starting tilt | Carrier range differences used | Median satellites per interval | Share of score-weight norm covered by the ground receiver | Linear range error allowance |
| --- | ---: | ---: | ---: | ---: |
| Original support | 2,496 | 10 | 99.98% | 1.97 mm |
| 0° | 1,672 | 5 | 97.4% | 0.29 mm |
| 5° | 1,527 | 4 | 90.0% | 0.20 mm |
| 10° | 1,388 | 4 | 95.5% | 0.16 mm |

Each screen retains a satellite only when its ray clears the modeled
antenna plane by at least 1° at both endpoints. The calculation removes
the common receiver clock from each new satellite set and recomputes
the weights for the original position score. It keeps all 240 intervals
and the original times and anchors.

A [follow-up weighting test](ESA_CARRIER_WEIGHT_TRADEOFF_RESULT.md)
kept exactly the same satellite sets and raised the screened allowances
to 1.35–1.71 mm by balancing range and motion error.

These are allowances for the linear range model with the tested
weighting and 1.876 mm/s² RMS allowed position-error acceleration.
They do not include uncertainty in the anchors, the nonlinear
range correction or the installed antenna response. The earlier
0.96 mm ground-covered error budget uses a different allocation of
uncertainty. [Full error budget](ESA_NKAR_ERROR_BUDGET_RESULT.md)

The original weights, per-pair minimum elevations and ground coverage
reproduced before screening. One task completed in 245 charged checks.
Nine focused software tests passed. The study ran zero new fits and
opened zero reserved flights.

[Frozen plan](ESA_CARRIER_ELEVATION_SCREEN_PLAN.md) ·
[Saved satellite sets, score weights and completion receipt](esa-carrier-elevation-screen-result.json)
