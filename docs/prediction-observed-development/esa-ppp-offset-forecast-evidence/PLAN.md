# Test whether past receiver offsets predict later ones

The [chronological receiver comparison](ESA_PPP_COVARIANCE_CHRONOLOGY_RESULT.md)
finds a sharp increase in relative offsets even though faster changes
still transfer. Test whether earlier observations of the relative
offset can predict later offsets within the same flight. Use the same
97 donor windows and 98 later windows and the same six contrast channels.

Represent each window by the six mean position differences in metres.
Fit a stationary independent reference, a random walk, and a set of
mean-reverting models with persistence times of 2, 5, 10, 20 and 40
two-minute windows. Use only adjacent donor transitions. The
mean-reverting models approach the donor mean exponentially and model
the covariance of innovations after scaling by the expected one-step
variance. The random walk carries the last offset forward and grows
innovation variance in proportion to elapsed time. Add a diagonal
ridge of one millionth of the mean innovation variance to each
covariance. Select the changing model with the best normalized donor
log score. Include the independent reference in every report.

Seal the donor results before reading the later contrasts. Score at
leads of 1, 4 and 12 original windows, using only the window at the
specified earlier index to set the changing-model forecast. Use all
later targets with a complete earlier and later window. Record the
actual elapsed time and every omission. Compare the two laws by log
score, RMS relative position error and mean squared standardized error.
The predictions overlap and are descriptive.

This tests a receiver consistency forecast when all three solutions are
available. It cannot estimate error common to the receivers, establish
accuracy from a single receiver or qualify another flight. Use frozen
position contrasts only, with zero new original reads, trajectory fits
or reserved recordings.

Use one frozen task on one thread with a 180-second limit. Charge 195
calls and steps for extracting the means, seven calls and 672 steps for
the donor candidates, and 294 calls and 588 steps for the later targets.
Permit one charged recovery attempt under a separate 180-second
allowance. Preserve the donor and score artifacts in order.
