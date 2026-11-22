# Matching-kernel rate comparison, separate finite study

The [first attempt](RATE_PROPAGATION_V1_RESULT.md) is terminal. Its baseline
failed because it used a different numerical kernel from the original saved
forecast. Do not modify or retry that attempt.

This new study repeats the same fixed question, selected ESA development
recording 187, three rate interpretations, saved 26-parameter fit, training
initialization, 800/400 split, model, clock and calibration bounds. It changes
one software dependency: use the **original extended-precision tangent kernel**.
The baseline must match the sealed forecast within 10⁻¹² in each stored
coordinate before the alternative trajectories may be interpreted. No
parameters are refitted and no later receiver value enters propagation.

Qualify the matching kernel on the sealed generated smoke forecast, then run a
three-task generated smoke through the study engine. Bind local tests, source
and numerical environment before preparing the observed run. Include the
shared task-recovery checks; completed task results and failures are never
repeated. The observed run has three tasks, one native tangent call each,
360,028 intervals and 1,200 queries, one worker/thread and a cooperative
45-minute wall allowance. Its initial maximum is **3 calls and 1,296,100,800
packet/query visits**. If interrupted, separately freeze a recovery with at
most one additional charged start per unfinished task. The seven confirmation
groups remain protected.

After all three tasks seal and the baseline passes, a saved-only reporter may
open the development receiver scoring rows and describe trajectory differences
and absolute errors. This is sensitivity at one saved fitted point, not an
instrument-phase determination, new Earth-model decision or calibrated
uncertainty statement.
