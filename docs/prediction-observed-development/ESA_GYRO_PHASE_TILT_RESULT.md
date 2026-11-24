# Aircraft turns can move the GPS phase score

On the two-minute ESA development comparison, the recorded turns allow an
ideal antenna phase correction of at most **10.7% to 22.8% of the saved
score gap** across three starting tilt assumptions. The real antenna's
phase response remains unmeasured. The earlier upright-antenna replay
gave a much smaller correction. [Upright replay](ESA_NKAR_PHASE_WINDUP_RESULT.md)

| Maximum starting tilt | Largest allowed tilt during the interval | Maximum share of score gap | Weight with all rays guaranteed above the antenna plane |
| ---: | ---: | ---: | ---: |
| 0° | 21.40° | 10.7% | 43.5% |
| 5° | 26.40° | 16.5% | 0.57% |
| 10° | 31.40° | 22.8% | 0% |

These are upper bounds across the allowed orientations. A tilt can exceed
a satellite's elevation even when the antenna began upright. The table
extends the ideal phase formula to rays below the plane when necessary.
It cannot establish the installed antenna's accuracy for those rays or
account for reflections. The percentages in the last column refer to
absolute endpoint score weights. They give the share of support whose
above-plane condition the calculation can guarantee.

The study used 36,001 saved gyro intervals and 241 carrier endpoints.
The largest logged change in orientation was 21.10°. The reported tilt
limits add the starting allowance, change in local vertical and one
nominal background-field-rate allowance. The calculation reproduces the
earlier full and ground-covered score weights.

One task passed with two charged calculations, zero new fits and zero
reserved-flight reads. Six focused tests of the new bound passed within
the 16-test antenna-motion regression.

[Frozen plan](ESA_GYRO_PHASE_TILT_PLAN.md) ·
[Endpoint bounds, input hashes and completion receipt](esa-gyro-phase-tilt-result.json)
