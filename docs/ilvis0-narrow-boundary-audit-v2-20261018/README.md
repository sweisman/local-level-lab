# The narrow timing branches

The completed boundary study passed both controls and both profiled-removal endpoints, including their repeat comparison. Both unsubtracted endpoints stopped before native side checks because their final timing branches were below the fixed minimum probe spacing. This is a numerical qualification failure, not evidence in favor of either surface model.

| Endpoint | Left width | Right width | Smallest probe | Probe distance in parameter ULPs | Clock states match |
|---|---:|---:|---:|---:|---|
| bias1_unsubtracted/primary | 20.9832 fs | 3.92186 fs | 0.245116 fs | 29 | True |
| bias1_unsubtracted/repeat | 20.9832 fs | 3.92186 fs | 0.245116 fs | 29 | True |

An ULP is the spacing between adjacent representable floating-point numbers. The fixed guard requires at least 2.13163 femtoseconds here. All saved side points are distinct representable values and reproduce their intended clock states. That supports qualifying a separate representability-aware probe check, rather than using a fixed normalized spacing for every timing value. The original failed checks remain failed. Correct clock-state geometry alone does not prove that native side derivatives, continuity or nuisance corrections pass.

A revised candidate must demonstrate independent known-answer behavior on narrow minima, maxima, discontinuities, unrepresentable branches and nuisance failures before a fresh finite observed-data test. Keep stationarity, cost, physical-position, source-preservation and repeat limits unchanged. Do not simply turn off the minimum-spacing guard.

This audit uses two saved endpoint artifacts and twelve clock-state queries. It performs zero native calls or fits, reads no original IMU data and changes no labels. Findings remain **50 globe / zero flat / three unresolved**.

[Completed boundary study](../ilvis0-remaining-boundary-20261018/RESULTS.md) · [Next analyses](../NEXT_STEPS.md).
