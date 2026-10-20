# Shared fixed-reference error-scale controls

**8/8 generated identities passed** in 4.19 seconds. No archive reads, model fits or withheld observations.

| Family | Covered / realizations | 99% coverage lower limit | Median upper scale / true scale |
|---|---:|---:|---:|
| central | 1016/1024 | 0.98308 | 1.2005295904175748 |
| reference_mean | 1013/1024 | 0.97912 | 1.1990304479749447 |
| small_noncentral | 1021/1024 | 0.99022 | 1.2313850794899137 |
| large_mean | 1024/1024 | 0.99551 | 873.3366703060747 |
| zero_rank | 1013/1024 | 0.97912 | 1.1959131824002347 |
| dependent_columns | 1019/1024 | 0.98725 | 1.2002265116303015 |
| correlated | 1015/1024 | 0.98174 | 1.2026503537692141 |
| smooth_mean | 1016/1024 | 0.98308 | 1.2249636827841206 |

The finite software gate is a 99% lower coverage limit of at least 0.97 for every family, around nominal 0.99 model coverage. The fixed reference can be wrong without making the scale upper bound anti-conservative under the stated Gaussian law. A wrong mean can instead make it very wide. Covariance shape, selection effects and airborne coverage remain unqualified.

[Mathematics](MATHEMATICS.md) · [Frozen scope](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
