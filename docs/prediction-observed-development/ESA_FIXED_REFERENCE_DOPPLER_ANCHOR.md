# Reykjavík Doppler start-time check

The [second execution](ESA_FIXED_REFERENCE_DOPPLER_EXECUTION.md) stopped
before solving any velocities. The clock report lists 60 changes from
the initial position. The original GPS positions include the initial
position and all 60 later epochs. The Doppler study must start at that
first position. It assigns both existing change series zero at the
anchor and verifies that the later times match.

The second execution and its charged setup operation remain sealed in
`data/esa-fixed-reference-doppler-v2`. The third freeze verifies the
input layout during preparation and tests the anchor and time checks
with known motion. It keeps the same inputs, solver, comparisons and
operation allowance as the second freeze.
