# Inspect the remaining curvature using saved derivatives

The completed native probes saved all 27 derivative columns at every one of
the 293 query epochs. Their reference derivatives are also preserved. Use
those existing arrays before proposing more integration or a larger study.

For each of the twelve fixed points, compare the observed change with:

1. The reference linear prediction.
2. The reference plus the retained shared-source terms.
3. The endpoint derivative average, applied to the same fixed parameter change.

Compare the first and third expressions at all 293 epochs. Shared-source maps
exist at only six saved epochs; compare all three expressions there without
interpolating or inventing maps for the other epochs.

The third expression approximates the line integral of the derivative between
the reference and probe. It is a diagnostic, not a certified error bound.
Decompose its curvature contribution by the original physical parameter groups.
Do not fit coefficients to the saved outcomes or adjust the points. Keep all
27 columns, training epochs and later predictions explicit and separate.

Proposed finite scope: twelve fixed-point comparisons over 293 epochs, or
10,548 coordinate comparisons for each derivative expression and 216 for the
shared-source comparison. Zero native calls, LP proposals,
aircraft reads or model-fit starts. Freeze source/input hashes and environment;
use one numerical thread with other allocations reserved and a 120-second
cooperative ceiling. Check known affine/quadratic examples and missing-column
failures before execution. Publish from the saved results only.

Use the outcome to identify a justified curvature/bounding change. Sampled
agreement cannot qualify nonlinear uncertainty coverage, the aircraft error
law or the whole prediction period.
