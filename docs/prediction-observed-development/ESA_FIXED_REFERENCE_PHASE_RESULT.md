# The two Reykjavík GPS paths disagree during the ground stop

The relative path from the aircraft and fixed receiver's carrier
measurements disagrees with the aircraft's original GPS solution.
Both paths start at the same first matched coordinate.

| Difference over 60 later matched times | North | East | Up |
| --- | ---: | ---: | ---: |
| RMS between paths | 0.27 m | 0.40 m | 0.85 m |
| Largest absolute difference | 0.32 m | 0.45 m | 1.02 m |
| Largest shift from omitting one of ten satellites | 0.77 m | 0.51 m | 1.19 m |

The position and clock fit had full rank at all 60 times. The phase
path starts to separate within 30 seconds. At the final match it
has moved 0.99 m up while the original GPS path has moved 0.01 m
down. These are relative path estimates. The comparison cannot assign
the discrepancy to one receiver. Continuous tracking flags alone do
not establish carrier measurement quality.

The main result includes all ten preselected satellites. The single
satellite omissions are sensitivity checks. The next test will look
at the two recorded carrier bands separately and keep every satellite
so changes in the error can be traced to specific measurements.
This stop has not qualified an uncertainty model for the aircraft.

Seven checks passed. The study used one task and one numerical thread,
with all 1,220 satellite states and 660 linear solves accounted for.
The original aircraft observations and the frozen study remain local.
The result includes each fitted displacement, residual, ephemeris
identity and satellite omission. No IMU flights or reserved sequences
were used.
[Frozen plan](ESA_FIXED_REFERENCE_PHASE_PLAN.md) ·
[Raw signal coverage](ESA_FIXED_REFERENCE_PAIR_RESULT.md) ·
[Verified derived results](esa-fixed-reference-phase-result.json)

To verify the published results against the completed local study, run
`env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_fixed_reference_phase report`.
