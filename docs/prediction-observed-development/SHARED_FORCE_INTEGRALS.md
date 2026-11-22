# Reuse the force integrals across report times

The height-aware predictor can build all force-integral reports from a
single pass through the packets. On a generated record with **4,096
packets and 24 query times**, all 24 reports matched the older calculation
exactly. Visits dropped from **98,304 to 4,096**. One local timing measured
17.118 seconds for repeated scans and 0.577 seconds for the shared pass.
The timing covers the force-integral calculation alone.

The benchmark repeated the 4, 6, 5 and 7 ms periods 1,024 times.
Queries ran from 0.5 to 12 seconds in half-second steps, with exact
clock windows of ±1/4,096 s. At packet index `i` starting from zero, the
three force coefficients were `(i % 19 - 9) * .00015`,
`(i % 13 - 6) * .0002` and `(i % 7 - 3) * .0004`.

The shared pass keeps one running state for complete packets and saves
the partial-packet states at each query. It still checks support on both
the binary packet clock and the exact duration sum. The tests compare
query windows on and around both kinds of packet boundaries, including
point windows and cases with rounded-tag gaps and overlap. The full
predictor checks retain the force bounds, the same compiled forecasts
and all the physical and auxiliary derivative columns.

Set `reuse_force_profiles=True` when preparing a new bounded run. Older
callers retain their original packet-visit accounting by default.

This change removes the repeated force scan. The initial-force rounding
check and the error bound at aircraft history lengths remain separate
qualification steps. [History result](SHAPE_GRAVITY_HISTORY_RESULT.md).
