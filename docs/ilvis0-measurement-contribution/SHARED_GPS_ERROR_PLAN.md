# Shared GPS height error on saved paired windows

Reopen the sealed position and receiver-window results for the eleven
existing pairs. Use their 490 saved targets and each receiver's original
selected width. Apply a quadratic second-derivative operator with equal
receiver weights on exactly matched epochs. Retain missing or incomplete
support. Leave the original window choices, positions and decoder outcomes
in place. Use no gyroscope, acceleration samples or ESA data.

Add a hypothetical 0.10 m sinusoidal height error to both receivers. Use
periods of 20, 60 and 120 seconds. These are sensitivity inputs, and none
is an observed value or a statistical bound. For the nominal receiver jet
and two quadrature components of the added error, evaluate the required
force for all four geometry/field combinations at 9.81 m/s² declared
gravity. Record the greatest possible force-vector shift over sinusoid
phase and sample 16 common phases to see what happens to the difference
in force magnitude between the globe and disc under the same field.
Phases are swept separately at each target. Changes across targets cannot
be counted as if they occurred under one shared phase.

The work is a saved-results calculation. The finite ceilings are 11 pairs,
490 targets, 980 receiver windows, 980 polynomial operators and 27,440
force predictions. There are zero aircraft fits, zero native fit calls
and no access to withheld ESA recordings. Use at most one numerical
thread. Verify that the added error cancels in paired heights, test the
derivative operator against the existing reference and preserve every
target disposition. This measures the sensitivity to an error that pair
differences cannot detect. A separate reference is needed to estimate
its actual size in aircraft data.
