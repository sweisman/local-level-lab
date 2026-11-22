# Earlier Reykjavík Doppler executions

The corrected study is documented in the
[completed Doppler comparison](ESA_FIXED_REFERENCE_DOPPLER_RESULT.md).

The direct Doppler check produced no matched path comparison. The
[first run](ESA_FIXED_REFERENCE_DOPPLER_EXECUTION.md) stopped on an
incomplete budget entry. The [second run](ESA_FIXED_REFERENCE_DOPPLER_ANCHOR.md)
stopped because the saved clock path starts one observation after its
anchor. Neither run estimated velocities.

The third run processed all 3,601 aircraft epochs and reached the first
fixed-station solve. The station header reader returns the position and
clock flag together. The adapter passed that pair to a solver that requires
only the three position coordinates. The worker sealed the error after
3,603 charged operations, including setup and the failed station call.
Aircraft velocities were held in memory until the matched comparison.
There is no saved aircraft velocity path from this run.

The revised study qualified the station header reader through the velocity
solver and sealed the receiver outputs separately. The three earlier execution
records remain sealed.
