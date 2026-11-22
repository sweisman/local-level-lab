# Four steady-course controls for the ESA turn study

Recording 187 has four unused steady-course windows that can be compared
with the four already scored turn windows. The choices use the saved GPS
course summaries alone. Each has 400 seconds for training and 120 seconds
for comparison with later positions.

| First receiver index of reference turn window | Steady-course control support | Upper bound on course variation during its 120-second forecast |
| ---: | ---: | ---: |
| 22936 | 21856–22895 | 1.33° |
| 33796 | 32716–33755 | 0.74° |
| 37516 | 36436–37475 | 1.02° |
| 41116 | 39916–40955 | 1.49° |

For each turn in recorded order, take the closest unused control in the
same continuous run. Break ties toward the earlier control. Bound course
variation from the four consecutive 30-second blocks, using each block's
span and signed change to allow for a heading trend between blocks.
Require a bound of 2° or less. Keep complete supports disjoint from one
another, the earlier development windows, the repeat-turn windows and
the staged solver comparison. This is a steady-course criterion based
on ground track. It leaves bank, climb and other aircraft motion open.

Reproduce the metadata check with
`env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_straight_control_windows`.
It verifies the inputs and produces the
[selection receipt](esa-straight-control-windows.json). It reads no
original measurements and runs no fits. Two tests cover the course
bound and full-support exclusions.

The [clock check](esa-straight-control-window-clock.json) verifies all
four supports on the original recording. It pairs 1,600 training
positions with 480 later timestamps. The largest inertial timestamp
gap was 3.334 ms. Later receiver positions and inertial motion readings
remained withheld. Add `--clock` to the command above to reproduce this
check. A third software test verifies continuity at the forecast cut.

For the next comparison, use the same reference forecast, both inertial
error descriptions and both training starts as in the
[turn study](ESA_REPEAT_TURN_FORECAST_RESULT.md). Freeze timing, prepared
inputs, software and recovery limits before running. Preserve the same
four error allowances. Compare the effect of adding the turn allowance
with and without the steady allowance. Record the actual angular motion
of the instrument even when GPS course stays steady. Release later
receiver positions only after picking forecasts by training cost.

The [input preparation](ESA_STRAIGHT_CONTROL_MATERIAL_PLAN.md) is ready
to run when one numerical thread becomes available.
The [forecast plan](ESA_STRAIGHT_CONTROL_FORECAST_PLAN.md) records the
matched cases and the original limits for the next stage.
The [release plan](ESA_STRAIGHT_CONTROL_RELEASE_PLAN.md) specifies the
score comparison and how to retain any missing forecasts.
The [timing check](ESA_STRAIGHT_CONTROL_TIMING_CHECK.md) tests whether
the same turn allowance helps when applied to a different part of
the recording.

All eight windows are from one development recording. A difference
between turns and steady-course controls can guide the aircraft error
model. Independent coverage and the reserved flight comparisons remain
separate.
