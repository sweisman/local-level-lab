# Bound the motion needed to align saved force directions

Reuse all 991 supported windows from the two matched recordings. In each
window choose the packet whose nominal-clock midpoint is closest to the
original GPS target. Use the same packet under both clocks. Evaluate the
existing fourth-degree trajectory approximation at the packet's actual
midpoint under each clock, with both receiver paths and all four candidates.
Keep training and later histories separate. Use zero calibration corrections
and retain the half-count acceleration uncertainty. Treat each fitted GPS
path as supplied and the packet vector as representative of its midpoint.
These are declared sensitivity assumptions. A packet mean need not equal
its instantaneous midpoint value, and the archive supplies no independent
rate limit or complete direction-error budget.

Report a pairwise lower bound and the rate of one verified nominal sampled
orientation path. Test the midpoint of that rate interval once with the
whole-history search, using 4,096 twist angles. Tighten the interval only when
that search excludes the midpoint even with count errors, or provides a
directly verified nominal path. Report the remaining width and every case.
Neither the required rate nor the verified path establishes actual aircraft
motion. No shape or angular-field decision follows from this diagnostic.

Freeze inputs, source and environment. Cap the replay at 1,982 existing path
approximations, 15,856 force-point evaluations and one grid probe per 64
histories. Use one numerical thread and zero new navigation fits or receiver
position solutions.
