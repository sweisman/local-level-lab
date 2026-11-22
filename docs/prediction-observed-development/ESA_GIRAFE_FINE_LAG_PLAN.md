# Compare the GIRAFE to iMAR lag at finer time steps

The three [ground force matches](ESA_GIRAFE_GROUND_RATE_RESULT.md) all
peaked 0.1 seconds earlier than the proposed time. The same change left
the middle [airborne clip](ESA_GIRAFE_PLATFORM_IMAR_FORCE_RESULT.md)
unmatched. Use exactly these six clips to measure whether one small shift
explains their force timing. This is a retrospective diagnostic. The
previous qualifications and the platform rate convention stay separate.

Keep the original force magnitudes and platform tenth-second cells. For
iMAR, use the same saved support and a 10-millisecond grid over the earlier
and later two-second guards. Integrate the original left-held samples over
those cells. Form elapsed-time-weighted tenth-second cells starting at each
possible lag in the grid. This changes where averaging begins without
interpolating sample values or modifying timestamps.

Compare first differences after averaging over 0.1, 0.3, 1.1 and 2.1 seconds.
Verify that the 1.1-second comparison reproduces every previously saved
tenth-second lag score within `5e-8` correlation. Select one common lag by
maximizing the weakest of the three ground correlations at 1.1 seconds.
Break ties by the shift closest to the original clock. Apply that lag
unchanged to all six clips. Report their original and common-lag scores,
highest correlations and best shifts at all four widths. Keep the previous
0.70 correlation reference visible. Neither the finer grid nor a high
correlation establishes a fine clock accuracy or an aircraft error law.

Use one local task and one numerical thread, with one verified original
iMAR hash pass, exactly six original range inputs, six iMAR slices of at
most 5,000 intervals each and 9,624 scored combinations over 401 lags.
Use a 120-second limit. No network reads, model fits, new motion selection
or reserved-flight work enter the task.
