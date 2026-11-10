# Comparing receivers on the same survey legs

Some selected survey legs have two recorded primary GNSS receiver streams at
the same time. Comparing them can show how much their reported positions differ
and whether that difference persists. Neither receiver is treated as the true
aircraft position.

The preexisting flight-group ledger has 12 overlapping pairs. Both receiver
streams passed the strict binary decoder for 11 pairs; the twelfth includes
the one saved receiver-decoder failure.
All 11 eligible pairs were analyzed. They are on 11 dates in 11 conservative
flight groups, which are not proven independent installations.

| Saved-data result | Value |
|---|---:|
| Pair tasks completed and passing | 11 / 11 |
| Exactly matched receiver epochs | 25,890 |
| Matches per pair, minimum / median / maximum | 1,045 / 2,569 / 3,420 |
| Later-half horizontal disagreement after an earlier-only constant offset, median (range) | 0.202 m (0.050–0.738 m) RMS |
| Later-half height disagreement after the same procedure, median (range) | 0.248 m (0.041–0.624 m) RMS |
| Median one-second correlation of the remaining north / east / up differences | 0.989 / 0.991 / 0.989 |
| Median five-second correlation, north / east / up | 0.949 / 0.908 / 0.899 |

The offset was estimated from the earlier half of each overlap and held fixed
when scoring the later half. Positions were paired only when their GPS time
tags were exactly equal; no interpolation, fused navigation or IMU data entered
the calculation. The per-pair results also retain the raw position differences,
reported receiver precision, gaps and exact lag support.

**What the close agreement means:** the two recorded position streams usually
track each other closely, and their differences change slowly rather than as
independent noise. The receivers' own reported one-sigma values, combined in
quadrature for description, have median north/east/up values of about
1.021/0.906/1.822 m across the pairs. The smaller observed differences do not
prove those estimates are too large: shared satellite, atmospheric or correction
errors can cancel in a comparison, and antenna separation or aircraft attitude
can add motion to it. Different file bytes do not establish independent
antennas or processing.

This is **relative receiver agreement**, not a measured absolute position-error
distribution or a calibrated receiver-plus-IMU prediction law. It does not
alter the 53-stretch Earth-model comparison or supply a significance level.
The next gate is to assess common errors and held-out aircraft predictions
under a stated combined error model. The reserved ESA confirmation recordings
remain untouched by model fitting.

The selection, method and finite limits were recorded before the 11-pair run.
Nine source-bound software checks and a saved first-pair check
qualified the implementation. An earlier unprepared definition lacked the
study engine's primary-input field; it was corrected and requalified before
any pair task started. The published study preserves its inputs, frozen code,
all outcomes and per-epoch differences.
