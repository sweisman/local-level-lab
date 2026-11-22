# Relative receiver differences at a forecast-length horizon

Use only the already opened ESA recording 187 and the three GNSS-only PPP
exports from the completed full-flight receiver audit. Hash-check the same
sources, strictly parse the one documented printed-counter rollover, match
within 2 ms without interpolation, and apply the existing velocity/time
adjustment. No inertial record, Earth-model fit or reserved flight group is
read.

Partition the full `air1` GPS-week timeline at multiples of 120 seconds. Keep
every matched pair in its assigned window. A window is labeled **fast** from
receiver speed alone when at least 90% of its matched `air1` reports have
horizontal speed at least 50 m/s and it contains at least 80 matched reports.
For each receiver and window, report count, fast fraction, north/east/up mean,
RMS, centered RMS, 95th absolute difference, and end-minus-start difference.
Summarize the distribution of fast-window RMS and mean drift. The 120-second
length matches the opened development prediction horizon; it does not imply
independent windows or calibrated error coverage.

The purpose is to see whether relative receiver disagreement stays small over
the same span as a withheld forecast. These exports share an antenna and
processing, so even perfect agreement cannot establish absolute position
truth. Do not use this result alone to select a scientific threshold or open
the reserved groups. One local thread and source-bound deterministic output.
