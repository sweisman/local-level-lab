# Training-only refit under three ESA rate interpretations

## Fixed question

Can any of the three plausible conversions from reported ESA iMAR rates to
increments give an adequate training fit and later prediction on development
recording 187, after the **same complete nuisance model** is refitted using
only earlier observations? The [fixed-point check](RATE_PROPAGATION_V2_RESULT.md)
shows 19–43 m later horizontal trajectory sensitivity, so a fixed fitted point
cannot settle this question.

Use the saved 360,029 reported rate samples and original 800/400 receiver split.
For each of left hold, right hold and linear points, fit both original IMU
error laws (*increment* and *point*) under the same `sphere_rotating` model,
processing assumption, `header_elapsed` clock, 26-parameter bounds,
training-only receiver error policy, start 0, numerical stopping rule and
200-evaluation ceiling. This makes **six predeclared tasks**. Recalculate each
method's initialization from its own earlier increments and receiver rows;
use no later receiver positions until all six fit/forecast artifacts seal.
The original linear-point fits and forecasts must be reproduced within a
predeclared numerical tolerance before the alternatives are interpreted.

The result is development **prediction adequacy**, not an Earth-model test.
Report every numerical failure. For every completed fit, report training and
later horizontal/vertical RMS and maxima, active bounds and stop reason.
Apply the same preset physical accuracy screen to all six. Do not choose the
instrument convention from later error, and do not treat the minimum training
cost among six variants as a calibrated selector. The seven independent ESA
confirmation groups remain unopened.

## Qualification, finite budget and recovery

First run a short generated six-task control that reproduces the original
linear-point saved fit/forecast and checks that later receiver rows cannot
reach training. Qualify the three input constructions, source/environment
bindings, finite accounting and task-level interruption recovery before
observed preparation. Keep each task separately sealed so a reboot does not
repeat completed work. An interrupted task may receive at most one additional
separately charged start under unchanged scientific inputs and method; a
completed numerical failure is never retried.

The observed study will use at most **three workers, one numerical thread
each**. Its initial finite allowance is one start per task, at most **700,000
native calls and 45 billion packet/query visits per task**, with a cooperative
four-hour wall cap for the whole initial study. Those ceilings accommodate the
200-evaluation numerical limit and the measured 601,895-call cost of a full
saved ESA error-operator construction; they are not expected consumption.
Across six initial tasks the ceiling is 4.2 million calls and 270 billion
visits. Recovery has a separate at-most-six-start ceiling, only for tasks
left technically unfinished, and no permission to retry a sealed failure.
The recovered total ceiling is therefore 8.4 million calls and 540 billion
visits. Source, numerical environment, original bytes, task IDs, charge
journals and outputs must remain hash bound and reboot verifiable.

The frozen study may finish with abstention. It must not relax the physical
accuracy screen or promote any result to the protected groups just because a
different rate interpretation fits better.
