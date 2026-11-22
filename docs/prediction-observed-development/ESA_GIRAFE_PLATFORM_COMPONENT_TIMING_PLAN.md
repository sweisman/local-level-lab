# Check the candidate GIRAFE clock against individual force channels

The original force-magnitude timing study failed its first-excerpt
anchor rule. The two later excerpts independently pointed to the same
offset. Use that offset as a fixed hypothesis to see whether the timing
information survives in the horizontal channels. This is a diagnostic
on the three captured ranges and the previously verified 10 Hz reference.
It preserves the original failed timing decision.

Treat the first and second platform values after the timestamp as candidate
horizontal accelerations. Compute time-weighted tenth-second averages
of each and of their horizontal magnitude. Compare first differences with
the corresponding first differences from the 10 Hz reference. Use the
same full-record correlation search and the same locked-offset check as
the original timing study. Compare each channel separately. Preserve the
global maxima, scores at the locked time, and signed amplitude estimates.
The candidate axes and clock offset are fixed. No new search over axis
signs, filters or time drift is part of this check.

Use one task, one thread and 45 seconds. Allow one verified read of the
local 10 Hz reference, three exact saved one-MiB slices and nine correlation
calculations of at most 234,193 reference positions each. The scope is
saved development data. Independent confirmation of UTC timing and the
angular-rate channels remains separate.

Version 1 stopped before reading any signals because two values for the
same tenth-second query differed by about 7 picoseconds in floating-point
representation. Version 2 uses a 10-nanosecond equality tolerance for the
two stored offsets. The original stop and zero charged checks are retained.
All clock agreement and correlation thresholds stay as specified above.

Version 2 completed locally. Two reported horizontal-magnitude peaks of
1.0 away from the candidate clock exposed poor numerical conditioning in
the rolling variance calculation. Version 3 calculates each window's
centered variance and dot product directly in bounded batches. A generated
test checks that a large excursion elsewhere in the reference cannot
hide a low-amplitude known match. Preserve both result files and retain
the same timing hypothesis, comparison thresholds and work allowance.
