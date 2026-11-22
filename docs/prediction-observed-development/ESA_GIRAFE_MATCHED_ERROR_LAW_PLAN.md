# Test error transfer after matching the instruments' time cells

Use the saved force magnitudes after averaging iMAR's vectors into
the GIRAFE sample cells. Keep the original eight windows and both
averaging widths. In chronological order, learn the mean offset and
covariance on the first four windows and score the last four.
Use the same independent and correlated error laws as the prior
chronological check.

Repeat the training with only the earlier windows whose saved
GIRAFE interrogation time remained at 0.020 seconds throughout
the window. Score the same later windows at both averaging widths.
All windows remain in the report, including the variable-interrogation
window. Its role here follows an observed discrepancy on this
development flight. This makes the comparison a check of how the
error allowances transfer, with no claim of independent validation.

Report the mean offset, its error on later windows, both working
95% ranges, standardized error and the Gaussian log score. This tests
the relative disagreement between two instruments. It does not set
absolute aircraft noise or identify the source of either instrument's
errors.

Freeze two width tasks, one thread, two operations per width and
a 60-second limit. Use the saved bandwidth report and inventory.
No original data reads, physical model fit or reserved flight.
[Earlier chronological check](ESA_GIRAFE_FORCE_ERROR_LAW_RESULT.md) ·
[Matched averaging](ESA_GIRAFE_FORCE_BANDWIDTH_RESULT.md)
