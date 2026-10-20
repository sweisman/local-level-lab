# Structured covariance software controls

Qualification **passed**: 3/3 identities in 14.92 seconds. No original reads, model fits or native integrations.

| Epochs | Columns | Setup | Whole whitening | Block forward + inverse | Cached storage | Process peak RSS |
|---:|---:|---:|---:|---:|---:|---:|
| 4,000 | 1 | 0.56 s | 0.12 s | 0.16 s | 1.50 MiB | 69.30 MiB |
| 64,080 | 27 | 8.59 s | 2.17 s | 2.98 s | 23.96 MiB | 177.16 MiB |

Cache storage scales linearly with epochs. Process peak includes Python, imported libraries and generated input/output matrices; it is not the cache size. Structured paths construct no whole-record covariance, factor or projection matrix.

These are supplied-covariance software checks. Covariance estimation, bounded parameter uncertainty, predictive adequacy and native streaming integration remain separate.

[Method](PLAN.md) · [Frozen benchmark limits](BENCHMARK_PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
