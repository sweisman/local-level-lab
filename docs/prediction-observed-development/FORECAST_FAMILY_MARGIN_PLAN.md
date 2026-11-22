# Check separation across alternate training receivers

Use the original three paths and the six completed alternate-receiver
refits from ESA recording 187. Use the one original profiled-removal
increment setting matched by the refits. Center each alternate forecast
with its corresponding earlier receiver positions. Keep the original
receiver precision inputs and work in the same physical coordinate
chart on the same 120 later report times.

For each model pair and each of the four declared covariance assumptions,
use the direction between the original two forecast means. Repeat after
projecting out the cubic error terms. Project each model's three saved
forecasts onto that direction. Compare the smallest projected value
for the second model with the largest for the first, allowing unmatched
receiver choices between models. Every mixture of a model's three saved
paths lies in its projection interval. Report the signed gap and check
the original path separation against the preceding fixed-pair replay.

This is a sensitivity limit for the nine saved mean paths and their
mixtures. It does not cover calibration changes outside them, shared
receiver errors or a different flight. Use four covariance operators,
24 pair margins, six sealed alternate forecasts and one thread, with
zero fits, no later receiver observations and no protected flight reads.
