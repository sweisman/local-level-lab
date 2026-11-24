# Position anchor uncertainty uses up the range margin after screening

The earlier improvement from reweighting the GPS measurements assumed
exact position anchors. With one metre of allowed error per anchor
coordinate and the other published example assumptions, **none of the
three screened cases has room for additional range error**, even if
the error in the ground-covered directions is set to zero.

| Range weights | Score change allowed per metre of anchor-coordinate error | Remaining ground-covered range allowance |
| --- | ---: | ---: |
| Original weights and original anchor bound | 0.02193 | 0.958 mm RMS |
| New weights, original satellite set | 0.02507 | 0.241 mm RMS |
| New weights, 0° initial tilt screen | 0.03748 | 0 mm RMS |
| New weights, 5° initial tilt screen | 0.03859 | 0 mm RMS |
| New weights, 10° initial tilt screen | 0.04748 | 0 mm RMS |

The new weights place less reliance on precise range measurements and
more reliance on the position anchors and motion limit. The calculation
propagates errors at all six anchors through the saved score and the
range geometry. It includes the nonlinear geometric remainder, the
observed aircraft score, 1.876 mm/s² RMS of trajectory error acceleration
and 2 mm RMS of range error outside the ground receiver's coverage.
The one-metre anchor allowance is an example. Its actual size still
requires an independent measurement.

The signed disagreement between aircraft and Nuuk Museum measurements
was **1.3%–3.5% of the score gap** with the new weights. That checks one
direction in the error budget. Shared aircraft errors and the installed
antenna response still need independent limits.

The replay reproduced the earlier 0.958 mm example and its signed
ground comparison before applying the four new sets of weights.
One task completed with 246 charged checks. Ten focused software tests
passed. There were zero new model fits and zero reserved-flight reads.

[Frozen plan](ESA_CARRIER_REWEIGHTED_BUDGET_PLAN.md) ·
[Signed scores, anchor weights and completion receipt](esa-carrier-reweighted-budget-result.json)
