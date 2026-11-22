# The best forecast-conditioned allowance is 2.25 cm

For the two saved ESA zero-field forecasts, the original forecast
conditioning allows **2.25 cm** of uniform position error per
coordinate in the affine comparison. Independent certificates put the
optimum between **0.0224792141 m and 0.0224796320 m** (rounded outward).
The difference between the bounds is about 0.42 micrometres.

| Version of the same forecast-conditioned search | Outcome |
| --- | --- |
| Dense conditioning map | Reached the 2,000-iteration cap, with no new certificate |
| Compact conditioning through 15 states at the cut | 25 interior-point iterations and 16 crossover iterations |

The compact calculation uses 23,400 conditioning entries in place of
432,000. The calibration boxes, all 102 calibration columns, the nine
smooth terms and the receiver weighting stayed the same. One
certificate verifies a direction that keeps the forecasts separated.
The other constructs a calibration and error witness showing that any
allowed direction loses separation above the certified upper bound.

The **12.18 cm** broader result gives the comparison free use of earlier
position coordinates. Under the original rule those coordinates enter
only through the forecast. The 2.25 cm bound falls below the **4.03 cm**
allowance used as a reference in the earlier integration-error check.
Repeating the same optimization cannot close that gap. The remaining
options require independently supported calibration restrictions or a
bound that accounts for how integration errors move together in time
and across axes. Aircraft prediction uncertainty remains unqualified.

One task completed in 7.85 seconds with five charged bound calls. Eight
software checks passed. There were zero new aircraft fits and zero
reads of reserved observations.

[Frozen plan](ESA_COMPACT_FORECAST_MARGIN_PLAN.md) ·
[Verified evidence](esa-compact-forecast-margin-evidence/README.md) ·
[Integration error budget](ESA_POSITION_BOUND_BUDGET_RESULT.md)
