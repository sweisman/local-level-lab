# Comparison with the strict longer-flight inventory

The [strict inventory](../ilvis0-distance-inventory/RESULT.md) found five
10-minute/50-km stretches on four recorded dates across 232 sources. The
[alignment-only ablation](RESULT.md) rescanned the 29 receiver/raw candidate
sources and found **the same five stretches on the same four dates**. Matching
on original source SHA-256, UTC start, UTC end and duration gives 5/5 exact
interval matches and zero ablation-only intervals. The segment IDs differ
because they bind different policy versions.

Thus the alignment flag alone did **not** exclude any additional track under
this long-duration rule. The original rejection tally of more than three
million flagged samples remains correct, but overlapping course, climb,
roll, duration and raw-support checks can still eliminate those same samples.
This comparison uses no Earth-model outcome and does not validate fused motion
when alignment is false. The receiver/raw inventory's 29 tracks still need a
separately justified motion and information gate; none was promoted here.
