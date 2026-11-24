# Reweighting recovers much of the range error allowance after screening

Balancing GPS range error against smooth errors in the flight path raised
the allowed linear range error from **0.16–0.29 mm RMS** to
**1.35–1.71 mm RMS** on the three screened satellite sets. That is about
six to nine times the earlier allowance. All cases use the same
two-minute ESA development comparison, exact anchors and
1.876 mm/s² RMS acceleration allowance.

| Maximum starting tilt | Earlier range allowance | Best tested range allowance | New score-weight norm covered by the ground receiver |
| --- | ---: | ---: | ---: |
| Original satellite set | 1.97 mm | 2.53 mm | 99.82% |
| 0° | 0.29 mm | 1.71 mm | 98.26% |
| 5° | 0.20 mm | 1.60 mm | 97.61% |
| 10° | 0.16 mm | 1.35 mm | 99.25% |

The earlier calculation tried to reproduce the position score from
linear range changes as closely as possible. The new weights leave
more of the score to the allowed acceleration error. They reduce the
effect of range errors enough to recover margin. The calculation
recomputed the remainder directly at the saved score times, accounting
for cancellation between signed contributions. It allowed velocity
to change freely at the exact position anchors to give a conservative
motion bound. All four satellite sets selected the same damping
ratio of 0.3 from the eleven declared settings.

These are model-based allowances for this development interval.
Actual shared aircraft errors, anchor accuracy and the installed
antenna response still need independent checks. The full error budget
has additional terms beyond the linear, exact-anchor calculation.
[Aircraft error budget](ESA_NKAR_ERROR_BUDGET_RESULT.md)
The [uncertain-anchor replay](ESA_CARRIER_REWEIGHTED_BUDGET_RESULT.md)
found no remaining range margin in the screened cases under the
published one-metre anchor-error example.

One task passed with 293 charged checks. Twelve focused tests passed,
including direct checks of the continuous motion response and the
damped least-squares calculation. The replay ran zero physical-model
fits and opened zero reserved flights.

[Frozen plan](ESA_CARRIER_WEIGHT_TRADEOFF_PLAN.md) ·
[All weights, sensitivity checks and completion receipt](esa-carrier-weight-tradeoff-result.json)
