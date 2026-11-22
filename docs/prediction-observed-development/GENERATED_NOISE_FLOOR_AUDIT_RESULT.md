# The generated path screen is tighter than its declared noise

The [saved eight-case audit](GENERATED_NOISE_FLOOR_AUDIT_PLAN.md) used the
cohort's earlier-only forecast covariance and known generated route. Under
the **assumed** noise law, even with calibration fixed, the square root of
expected squared horizontal error over the later 300 seconds is **17.39 m**
for each case. The inherited deterministic screen requires **0.1 m**. The
expected error scale is about 174 times that screen.

| Generated law | Cases | Raw fitted path error | Earlier-conditioned center error |
|---|---:|---:|---:|
| Increment | 4 | 109–197 m | 20–30 m |
| Point | 4 | 67–182 m | 7–66 m |

Ranges show horizontal RMS across the four noise seeds per law. Conditioning
on earlier receiver observations improves every case, but none of the saved
centers is within the inherited 0.1 m screen. The 17.39 m figure is a
second-moment scale, **not a deterministic minimum or a measured aircraft
error**. It excludes uncertainty in fitted calibration; the actual raw-path
miss can be much larger. The eight cases share one route.
Even if these eight cases were independent draws from a fixed population,
eight successes would give only a 31.2% one-sided 95% upper bound on failure
probability; their shared route narrows the inference further.

The clean-data accuracy rule is therefore unsuitable as the sole pass gate
for these noisy generated forecasts. This does **not** explain the excess
raw-path error or validate the assumed covariance on real aircraft. A new,
separately frozen qualification must judge physical prediction against its
declared noise and calibration uncertainty, with absolute adequacy and
empirical coverage checked separately. The frozen eight-case failures and
all earlier results remain unchanged. No new fit or aircraft data were used;
the scientific decision remains **abstain**.

[Machine report](generated-noise-floor-audit-result.json) ·
[Original cohort](GENERATED_BOUNDED_COHORT_RESULT.md)
