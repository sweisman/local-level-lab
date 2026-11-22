# Average each GPS force prediction over the retained packets

Use all 991 supported windows from the frozen [packet audit](MATCHED_FORCE_SUPPORT_RESULT.md).
Reuse the same packet identities, GPS fixes and training split. Fit the same
quadratic path separately to each of the three receiver streams. Evaluate all
four models at the previously used apparent gravity and background fields.

For each clock, average the predicted continuous force magnitude over the
retained packet interval. Use eight equal subdivisions and enclose every
common timing offset from −0.15 to +0.15 seconds. Report the interval's
width and its difference from the old center-of-window prediction. For each
field, keep the globe–disc difference as an interval. In comparing those
intervals, independent endpoints give a conservative bound even though the
models share one timing offset.

Allow 23,784 mean-force envelopes and 190,272 interval evaluations on one
numerical thread. Freeze the sources and inputs before reading results.
These are GPS-derived path predictions. Receiver-stream differences test
processing sensitivity. A later comparison with measured accelerations
still needs a bound on shared receiver error, trajectory approximation and
accelerometer calibration. No new solves or fits are allowed here.
