# Compare the original and processed GIRAFE timestamps at the start of the recording

Both [range requests](ESA_GIRAFE_LEVEL1_CLOCK_PLAN.md) returned the start
of the processed export. Use the longer saved response for a separate
local check. This can test whether the two exports contain the same
vertical values on the same clock near the start of the recording.
Timing during the planned airborne intervals remains a separate check.

Freeze the SHA-256 of the original 187a acceleration file, the longer
response and its independently saved prefix. Verify that the response
starts with the prefix. Use exactly 1,320 processed records in GPS week
2269, from 384898.51739992 through 385030.41739992 seconds of week.
Compare each of two consecutive blocks of 660 records against the
original vertical acceleration. Convert original UTC to GPS time with
the flight-day offset. Match only by timestamp, using the nearest
original record at each of 41 shifts from −2 to +2 seconds in 0.1-second
steps. Check one-to-one matching within 0.05 seconds of each shifted time.

Preserve every comparison. Report RMS, mean and maximum absolute force
disagreement and timestamp offset. Call the records consistent with
copied samples only if the same unique shift has at most 0.000001 m/s²
RMS in both blocks. Use the original signs, no estimated force offset
and no interpolation. A match cannot identify physical sensor latency or
timing of the horizontal quartz channels.

Allow one local task, one numerical thread, one scan of at most 240,000
original rows, 82 comparisons and 30 seconds. Use zero native calls,
model fits, new downloads or protected recordings.
