# Check relative aircraft motion against the fixed receiver

Use the ten GPS satellites with uninterrupted dual-frequency records
across the [61 matched times](ESA_FIXED_REFERENCE_PAIR_RESULT.md). Freeze
the two excerpts and the original aircraft GPS solution before computing
any path. Anchor the aircraft geometry at only its first matched PPP
position, and use the fixed station's original RINEX header coordinate.
Start at the first exact matched epoch. Use the broadcast
navigation data for the same day and preserve the chosen ephemerides,
signal transit times and both elevation series. Apply the same geometry
conventions to the two receivers.

Convert each carrier measurement to metres and combine the two bands
to remove the first-order ionosphere term. Difference between the two
receivers, then in time from the first epoch to remove the constant
phase ambiguity. A common term across satellites represents the
receiver clock change. Fit it with the three coordinate changes, using
equal weights on the satellite differences. Use the highest minimum
elevation among the continuously tracked satellites as the named
reference for the reported double differences. Fitting the common
clock jointly accounts for the shared reference term.

Compare recovered displacements with the original aircraft GPS
solution at the same times. Report residuals, geometry rank, and
the effect of omitting one satellite at a time under a fixed rule.
This measures relative changes over one previously selected ground
stop. It gives no aircraft antenna survey, no noise coverage claim and
no independent-flight result. Freeze a finite work allowance and test
the method on known displacements with unrelated clock shifts and phase
ambiguities before running the aircraft comparison.

Use one task on one numerical thread. Charge one input check, 1,220
satellite states across the two receivers and 660 linear solves across
the 60 later epochs, for 122 charge groups and 1,881 work steps. Stop
if a required signal, ephemeris or rank is
missing. Use a 180-second cooperative ceiling and one separately
charged technical recovery attempt. No aircraft IMU or reserved flights
enter this study.
