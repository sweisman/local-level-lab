# What the training data leave open about accelerometer gain

Use the two added NASA recordings and all 24,072 sealed force envelopes.
Keep their earlier/later split, clocks, three receiver tracks and four model
settings. Make no new trajectory or inertial fits. The existing one-sided
screen requires the measured lower force to be no larger than the predicted
upper force after a single nonnegative gain correction of at most 15%.

For each recording and candidate, calculate the entire gain interval admitted
by the earlier screen. Check whether the later screen fails for every member
of that interval or only for the minimum gain. The later gain range describes
compatibility. It is never applied to recompute a forecast.

For each same-field shape pair, compare its two required force intervals on
each later window. Allow one relative scale for the whole history, from the
two earlier gain intervals. Minimize the worst separation between the scaled
intervals. Report a lower and upper bracket from monotone bisection. Use each
of the six clock and receiver choices separately, then require one scale
across all six as a sensitivity check. The objective is expressed in the
globe candidate's force units before its gain. Each force interval already
includes the original time-offset envelope. The interval calculation permits
more freedom than a single realized trajectory and clock offset.

Freeze two single-thread tasks, 14 shape profiles and four one-sided checks
per recording. Limit each profile to 48 bisection steps and the workers to
120 seconds. Use the previously qualified recovery policy under a 180-second
recovery limit. Verify interval endpoints and the gain split on known-answer
inputs. Keep all four candidates and both clocks. The results describe how
much contrast survives this scalar calibration rule. They supply neither an
aircraft error bound nor a curvature decision.
