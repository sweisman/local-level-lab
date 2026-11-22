# Where the late parallel-receiver divergence occurs

The [full opened-flight comparison](FULL_PARALLEL_GNSS_V2_RESULT.md) found
a large `mosaic03` difference in its eighth fixed window. That window also
contains a final ground stop. Before describing the discrepancy as airborne,
classify **every matched point in that window** by the reference `air1`
receiver's own speed, without looking at the difference:

- Fast: horizontal speed at least 50 m/s.
- Low speed: horizontal speed at most 0.5 m/s and absolute vertical speed at
  most 0.2 m/s, matching the existing ground-control rule.
- Transition: every other point.

Use the same source hashes, strict parser with explicitly verified printed
counter rollover, 2 ms time matching and first-order velocity-time correction
as the full comparison. For each of the two other receivers and all three
phases, report matched count, time span, adjusted north/east/up mean, RMS,
centered RMS and 95th absolute percentile. Require that phase counts add
exactly to the saved eighth-window match count. Do not drop outliers or
change the phase boundaries after viewing receiver differences.

This is an exploratory localization of **relative** receiver disagreement,
not an independent true-position estimate, error-law calibration or Earth
model test. No IMU, fits or reserved ESA groups. One thread; three source
hash checks and parses. A failed phase audit does not change the full-window
result.
