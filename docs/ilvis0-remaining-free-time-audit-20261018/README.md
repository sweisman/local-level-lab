# Why the remaining free-time fits stopped

Both fresh controls passed. All four target fits completed their calculations but failed the unchanged full stopping gate. The study used 198 of its 342 permitted native calls; it did not run out of its overall allowance. Primary and repeat predictions agree to roughly micrometres within each processing case, which establishes repeatability at these endpoints, not convergence.

| Processing case / start | Endpoint stationarity | Fresh check | Nearest boundary |
|---|---:|---|---:|
| bias1_unsubtracted / primary | 0.000224396 | not_stationary | 11.6291 ns |
| bias1_unsubtracted / repeat | 0.0002244 | not_stationary | 11.6291 ns |
| bias1_profiled_removal / primary | 1.65829e-05 | fresh_position_probe_not_stable | 60.9783 ns |
| bias1_profiled_removal / repeat | 1.66008e-05 | fresh_position_probe_not_stable | 60.9783 ns |

The endpoint stationarity limit is **0.0001**. Without fitted upstream field removal, only timing exceeds that limit. With removal fitted, endpoint stationarity passes, but the fresh correction changes the cost too much and produces a new stationarity failure. Its position changes are within the existing millimetre RMS limit. The broad “position probe” failure label therefore does not mean that the position limit itself failed.

The next useful numerical test should distinguish the two failure mechanisms. For timing-only endpoints, the existing source-preserving clustered-boundary checks are a candidate. For the profiled-removal endpoints, inspect the fresh correction direction and clock-branch crossings before choosing a correction. Neither diagnosis justifies a relaxed stopping rule or automatic acceptance.

This audit reads sealed endpoints and saved observation times only. It uses no original IMU records, native predictions or optimizer starts. The completed trial remains frozen. Published findings remain **50 globe / zero flat / three unresolved**.

[Source trial](../ilvis0-remaining-free-time-v2-20261018/RESULTS.md) · [Next analyses](../NEXT_STEPS.md).
