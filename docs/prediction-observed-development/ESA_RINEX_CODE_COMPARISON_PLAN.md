# Compare the sealed ESA GPS code positions with the receiver export

Use the sealed 1,041-epoch GPS code reconstruction and the existing 400/120
development comparison on ESA recording 187. Match each of the original 520
receiver reports to one distinct half-second code epoch within 1 ms. Repeat
the match with the recorded receiver clock offset subtracted from the raw
epoch marker, as specified for an unapplied offset in RINEX. Require identical
epoch assignments and report the largest time difference under both readings.
Do not interpolate, align position offsets, fit a time lag or choose a
method from observed errors.

Compare both code paths with the original receiver export in the local
north, east and up directions. Report signed mean and RMS separately for
the earlier 400 and later 120 positions. Rescore the same six already sealed
forecasts from the two complete settings on the later 120 positions using
each code path. Use the same ranking and descriptive position screen as in
the three-export comparison. Keep the other two settings unresolved as before.

Bind the source and numerical environment, verify all saved input hashes
and run on one numerical thread. Allow zero new fits or forecast
propagations. Keep the seven reserved ESA flight groups closed. The two code
paths use the same antenna and overlapping GPS measurements as the export.
Their comparison tests processing sensitivity on one development flight.

[RINEX 3.04 clock convention](https://files.igs.org/pub/data/format/rinex304.pdf)
· [Code reconstruction](ESA_RINEX_CODE_RESULT.md)
· [Previous three-export check](ESA_ALTERNATE_PPP_SCORING_RESULT.md)
