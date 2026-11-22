# Full-flight receiver comparison with explicit sequence rollover

Keep the three source files, eight air1 windows, 2 ms matching tolerance,
velocity-time correction, output statistics and limits from the
[first plan](FULL_PARALLEL_GNSS_PLAN.md). Its strict parse failed at the
documented `mosaic03` counter transition. Preserve that failure.

Only for the documented `mosaic03` export, allow exactly one printed
`00099999` → `00000000` transition. Require its GPS time to increase in the
same week, and require every other printed sequence and time to increase.
Extend sequence numbers by 100,000 after the transition for the existing
strict parser; preserve each original eight-character sequence in the parsed
record. All other receiver fields must remain byte-for-byte unchanged.
Require zero transitions in `pwrpak7`. A different wrap count, reverse time,
truncated row or malformed layout fails. This handles a logging counter,
not a scientific-measurement repair or interpolation.

Bind the source and helper hashes and verify the all-record sequence audit
before publishing the eight-window comparison. Zero fits, zero reserved
group reads, one numerical thread. The earlier 400-epoch result and the
first failed full-flight attempt remain unchanged. Agreement among receivers
sharing an antenna is relative, not true-position accuracy.
