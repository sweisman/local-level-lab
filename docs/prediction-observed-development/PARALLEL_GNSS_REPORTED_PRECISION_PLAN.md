# Compare receiver disagreements with their reported precision

Use only the already opened ESA 187 GNSS-only PPP exports. Keep the exact
hash-checked sources, strict printed-counter rollover, 2 ms matching and
velocity/time correction from the completed full-flight audit. Reuse the
saved, receiver-speed-selected 120-second **fast** windows unchanged. No IMU,
Earth-model fit or reserved flight group is read.

For each matched `air1`/other PPP pair within a fast window, divide the
adjusted north/east/up position difference by the square root of the **sum**
of the two exports' reported variances on that axis. Do not add the project's
research covariance floor, infer cross-receiver independence, or interpret
these as statistical z-scores. Report counts, median, 95th absolute ratio,
maximum and fraction with absolute ratio above 3. Also retain per-window mean
differences and mean reported standard deviations so sustained offsets are
visible. Require that every pair in each saved fast window is accounted for.

The summed variance is a descriptive reference scale. The exports share an
antenna and processing; their errors can be correlated, and reported PPP
precision is not an absolute accuracy guarantee. A large ratio flags a
relative inconsistency to investigate; a small ratio would not certify the
receiver error law. This is a one-thread local audit with no calibrated
Earth-model decision.
