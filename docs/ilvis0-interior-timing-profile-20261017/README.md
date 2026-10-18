# Map the time-alignment ambiguity

The closest-to-complete stretch has two repeatable nuisance fits at different
time offsets. This study fills in three intermediate offsets, fitting from both
verified starting solutions at each. It tests whether the cost changes smoothly
between the saved solutions or hides competing solutions that a local solver misses.

The six fits use the same measurements, physical bounds, receiver weights and
stopping checks. Their combined ceiling is 486 native calls, with four numerical
threads and no retries. Fixed-time completion cannot qualify a free-time fit or
change the published model comparisons.

Completed: all six fits passed, using 36 native calls in about fourteen minutes.
Both starts agreed at every intermediate offset. Cost rises and falls between
the sampled times, so a single local fit need not reach the same solution from
different time offsets. The [profile-seeded free-time trial](../ilvis0-profile-seeded-trial-20261017/README.md)
tests initialization from the complete verified grid with time released again.

[Results](RESULTS.md) ·
[Finite plan](PLAN.md) · [Verified endpoints](../ilvis0-profile-verification-20261017/RESULTS.md) ·
[Current findings](../CURRENT_STATUS.md).
