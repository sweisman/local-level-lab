# Check whether the earlier Nuuk phase correction carries over to later observations

Use all 17 preselected permanent Nuuk matches and the eleven GPS arcs
continuous across the checked periods. Use one saved continuous aircraft
carrier path, one fixed ground coordinate and the same broadcast navigation
and atmosphere model at all times. Measure the ionosphere-free phase
residual once per consecutive 30-second interval, after removing one common
range offset at each receiver. [Intake](ESA_NUUK_GROUND_INTAKE_RESULT.md) ·
[Saved aircraft path](ESA_CARRIER_PHASE_CONTINUOUS_RESULT.md)

Estimate one ground-subtraction multiplier on the first 13 matched times
only. Omit the interval containing the previously recorded aircraft clock
step. Leave the transition into the final four times out of both groups.
This gives 11 earlier intervals and three later intervals with no shared
epoch. At the later times compare no ground correction, unit subtraction
and the earlier multiplier held fixed. Repeat the calculation on the
individual L1 and L2 band residuals as diagnostic controls, and report any
broadcast ephemeris changes. No model state or aircraft path is refitted.
[Clock step](ESA_CARRIER_CLOCK_STEP_RESULT.md)

Use one worker, one thread, 17 modeled epochs and one final comparison,
with a 90-second cooperative cap and the existing qualified technical
recovery. Bind the exact prior coverage, observation inputs, path and
tests. This is a chronological development check on one flight. It can
show whether earlier ground information helps later range agreement. It
cannot certify absolute aircraft position errors or population coverage.
