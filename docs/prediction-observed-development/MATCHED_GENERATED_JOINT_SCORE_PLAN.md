# Test whole-path rankings against known model labels

Reuse the twelve sealed generated histories with all three models fitted
to identical earlier observations. Apply the same full and reduced drift
laws and both receiver weighting cases used on the ESA flight. Use each
history's unchanged 79/40 split. Construct all earlier-only range centers
before opening the later receiver material. Recreate the original seeded GPS
errors from saved truth and verify the complete earlier prefix and original
later scoring results. Read the true model label only for result accounting.

Use the fixed earlier coordinate scale and complete conditional joint score.
Compare the lower-score globe with the disc and assess the two globe models
only if shape favors globe. Count ties and wrong rankings as well as correct
ones. No cutoff is chosen. Compare all four error-law and weighting settings
separately. These are retrospective known-model controls on short simulated
paths, with no transfer of a threshold to observed flights.

Freeze the sealed study, source, environment and both law definitions. Use
twelve original receiver-draw reconstructions, at most 48 covariance operators
and 144 condition-and-score cases, one thread, zero fits, no new seeds and no
aircraft or reserved-group reads.
