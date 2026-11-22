# Check vertical force at longer averaging times

Keep the three [vertical holdouts](ESA_GIRAFE_PLATFORM_VERTICAL_HOLDOUT_RESULT.md)
and their fixed clock offset. All three selected the same discrete time,
and only one passed the original correlation test. Check how much the
agreement on the same measurements depends on the averaging time.

Verify the sealed holdout receipts and repeat their time-weighted 10 Hz
force construction. Use the original nearest reference start. Check that
the one-sample comparison reproduces every locked correlation. Then apply
the same moving average to both force series, at widths of 0.3, 0.7 and
1.1 seconds, and compare their first differences. Report correlation,
the scale of each series and the centered difference between them at every
width. Restrict each calculation to complete shared averaging supports.

The clock, source excerpts and channel mapping stay fixed. There is no
new search over lags or averaging times. This is a response diagnostic
on the previously scored excerpts. It leaves the original clock test
intact. A future timing qualification would need its own prior rule and
independent held-out data.

Use one local task, one thread and 30 seconds. Charge one verified 10 Hz
reference read, three one-MiB range reads and twelve bounded comparisons
of at most 400 samples each. Read only the locally saved data from the
opened flight. No network calls, model fits or reserved group reads.
