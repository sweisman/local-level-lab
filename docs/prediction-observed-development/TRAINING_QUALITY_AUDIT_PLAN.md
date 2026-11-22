# Receiver-quality association check on saved training data

Use the two sealed ESA 600-report development fits, their saved training
receiver rows and forecast training-coordinate differences. Verify the
recorded height difference against forecast minus receiver height. Compare
both raw height differences and whitened fitted height residuals with saved
PDOP, satellite count, reported height standard deviation and receiver
vertical speed. For each pair report ordinary Pearson correlation, first-
difference correlation and Pearson correlation after separately removing a
cubic trend in report index. The three descriptions are sensitivity checks,
not independent samples or a selected best adjustment.

No new fit, original measurement read, later receiver report or reserved
flight group. Do not interpret a correlation as identifying sensor versus
receiver error: quality, motion and residuals can all change with time. The
scientific decision remains abstain.
