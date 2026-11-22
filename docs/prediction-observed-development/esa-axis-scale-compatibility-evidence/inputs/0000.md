# Check whether the full range of separate scales can cover the ESA windows

Use the eight saved forecasts on ESA development flight 187. Preserve both
inertial measurement error laws, the forecast positions, the added covariance
roots, the motion response and the existing joint error reference from the
[axis-scale comparison](ESA_AXIS_INNOVATION_SCALE_RESULT.md).

Each axis can use any quiet variance multiplier from `exp(−5)` to `exp(5)`.
First check all four steady windows, which have zero motion response. Next,
unless the steady windows already rule the model out, check all eight windows
with separate quiet and motion scales for each innovation slot. The motion
scales have the same limits. A single setting must cover the windows within
each comparison. This retrospective search is more permissive than predicting
an omitted pair from other windows.

Increasing any scale adds positive semidefinite covariance, so the joint
squared error cannot increase. Use opposite corners to enclose scores within
each log-scale box. Keep the original lower and upper score limits. Check the
midpoint for a compatible setting and independently verify any such setting
with the saved likelihood. Otherwise split the widest log-scale span. Exclude
a box only when a corner bound proves that at least one window misses the
reference throughout the box. Return unresolved if the allowance ends with
open boxes. Verify both score bounds using the covariance solve residual and
retain the split tree and all reasons for exclusion.

Use two one-thread tasks, one per error law, with up to 512 steady boxes and
1,024 all-window boxes each. Use a 180-second cooperative cap and the existing
qualified recovery policy with a 240-second recovery allowance. Known-answer
tests must cover covariance, compatible and incompatible cases, and allowance
exhaustion. No forecast is recomputed. The result cannot qualify prediction
coverage or authorize opening a reserved flight.
