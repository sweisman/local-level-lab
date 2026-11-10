# Overlapping primary-receiver streams

## Question

How closely do two recorded primary GNSS receiver streams agree when their
selected stretches overlap, and how persistent is their difference? This is a
receiver-error diagnostic for the prediction roadmap. It is not an Earth-model
fit, an independent position truth, or a calibration of absolute GPS accuracy.

## Fixed selection

Use every `utc_overlap` edge in the existing
[flight-group ledger](../analysis-provenance/README.md). It has 12 such edges.
The completed [binary receiver inventory](../ilvis0-trimble-position-precision/recorded-inventory/README.md)
accepts both streams on 11 edges; the twelfth contains its one saved decoder
failure and remains in the denominator. No pair is selected by its position
difference, model result, or reported precision. A preliminary look at the
first pair by ledger order found 2,378 exactly shared receiver epochs and
sub-metre raw differences; that look does not change selection or thresholds.

Use only the saved per-epoch binary receiver-position tables and their frozen
source/qualification receipts. Match equal GPS week and millisecond tags
exactly; do not interpolate or substitute Group 1 fused navigation. Each pair
needs at least 100 common epochs to return a descriptive result. If it lacks
them, retain the failure. Original `.013` files, IMU samples, Earth-model
residuals and reserved ESA recordings are outside this study.

## Computation and interpretation

Convert matched receiver coordinate differences to local north/east/up metres
using the stated WGS84 receiver coordinate metric at each matched midpoint.
This metric is used only to express two receiver positions in metres. Split the
matched time series at its midpoint. Estimate one constant three-axis offset
from the earlier half; report raw differences and later-half differences after
that fixed offset. Do not fit a changing offset or use withheld epochs to
change the offset. Report exact-match counts, time gaps, per-axis median,
median absolute deviation, RMS, selected lag correlations and both streams'
reported precision. Missing lag support is reported as unavailable.

Different source files and byte streams do not prove independent antennas or
independent GNSS errors. Unknown antenna lever arms, aircraft attitude and
shared satellite/correction errors can affect the differences. In particular,
a small inter-receiver difference cannot validate either receiver's absolute
one-sigma field, and these overlapping pairs are not independent flight
replications. No acceptance threshold for Earth-model prediction is derived.

## Gates and finite execution

First qualify the calculation on generated exact-tag, offset, missing-tag,
clock-gap and known-correlation controls, including a standalone frozen-worker
load. Source-bind a saved check of the first ledger pair's 2,378 exact matches
without selecting on its position differences. Then freeze a study with 11
pair tasks, one worker, one numerical thread, 900 seconds maximum elapsed
time and zero model/optimizer/native evaluations. Save each result or failure
once, with source, input and environment hashes. Publish only sealed outcomes;
do not refit, repair a receiver stream, retry a failed task or change a gate
inside the freeze.

The next research gate after this diagnostic is independent assessment of
common-mode receiver error and full receiver-plus-IMU prediction covariance.
