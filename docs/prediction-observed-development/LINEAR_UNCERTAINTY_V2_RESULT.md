# Second local-uncertainty task stopped before native forecast

The corrected ESA development task built the full error operator and
replayed the sealed early cost and determinant, but ended **terminal** before
generating a forecast derivative. Its adapter supplied `ConditionalBounds`
to `TangentProblem`, whose constructor requires the base `Bounds` type.
This is a source-level interface error; the task did not test the derivative
or fitted-parameter uncertainty. The one start and full finite allowance
remain charged and preserved under its frozen identity.

A separate task will construct the forecast problem with the original base
bounds, then require the same fitted-point position and whitened-Jacobian
replays before attempting the local uncertainty calculation. No later GPS
report or reserved ESA group entered the failed worker. The scientific
decision remains **abstain**.
