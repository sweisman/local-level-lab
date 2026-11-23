# Compare the reserved training conditions with the development flight

Use the seven fixed one-second query layouts and the matched 400/800
training split on development recording 187. On each flight, summarize
the 800 earlier receiver rows and their last 400 rows. Keep the identical
120 later clocks to verify the split. Use the training-only receiver
reader, which decodes no later position, velocity or covariance values.
Use no inertial values, model fit, model score or fit outcome. Select no
new slice, rule or error case from the resulting differences.

For each split report the 5th percentile, median and 95th percentile of
horizontal speed, ellipsoidal height, absolute vertical speed, absolute
receiver course rate, satellite count, PDOP and reported height standard
deviation. Use shortest signed course differences and the actual time
steps. PDOP describes satellite geometry. Reported height standard
deviation describes receiver weighting and does not measure accuracy.
Report which reserved medians fall outside the central 90% of the same
quantity on the development split. This is a descriptive comparison to
one development window. It adds no eligibility or accuracy threshold.

Allow one pass through the acquisition-verified receiver export for
each of eight records, with fixed byte and row caps and one numerical
thread. Bind the exact earlier/withheld time hashes, source hashes,
software tests and environment before computing the profiles. Save
only aggregate summaries and hash receipts, with zero decoded later
observations and zero protected outcome reads.
