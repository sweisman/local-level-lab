# No single shared error block explains most of the width

All 24 conditional cases retained the known simulated outcome and passed their
support checks. Fixing the force-matrix error to its exact simulated value
reduced widths by 1.2–11.4%; its median height reduction was 7.3%. Fixing the
acceleration remainder reduced height widths by a median 4.1%. Fixing either
the reference or acceleration/clock block changed widths by less than 0.003%.

These effects are not additive. Supplying exact values unavailable for a real
calibration does not create a valid prediction interval. The result suggests
that refining one shared-error block alone is unlikely to resolve the bottleneck.

The next test will use the training constraints jointly to bound the combined
initial acceleration. Individual calibration coordinates can remain uncertain
while their combined effect is much better constrained. The propagation code
currently bounds that combination from separate coordinate ranges, potentially
losing this information. No new aircraft fits follow from this diagnostic.

**Accounting limitation:** the original plan allowed 576 exact support
evaluations, but omitted 144 source-certificate rechecks. The executed code
therefore used 720. All 24 identities, 144 LP proposals and the 300-second
runtime limit were respected; runtime was 54.4 seconds. The original freeze
and outcomes are preserved, and the check allowance is not retrospectively
expanded. This remains development diagnosis, not a qualification result.
See the [full accounting](ACCOUNTING.md).

[All conditional ranges](README.md) · [Next test](NEXT_PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
