# Separate receiver offsets from change within flight windows

Use only the sealed 120-second parallel-GNSS result and its unchanged source
hashes. For each of its 195 receiver-speed-selected fast windows, use the
saved relative-position mean, centered RMS and total RMS. Verify the identity
`RMS² = mean² + centered RMS²` on every axis and window. Across all fast
windows, weight squared terms by the number of matched positions and report
the fraction of total relative mean-square disagreement due to persistent
window means. Also report the 95th-percentile absolute window mean and
centered RMS separately. Keep both exports separate.

This audit does not read original receiver or IMU files, fit an Earth model,
estimate absolute GNSS error or consume reserved flight groups. It is a
descriptive check of what sort of **relative receiver discrepancy** the
aircraft error-law qualification must allow. It cannot rule out a shared
receiver error.
