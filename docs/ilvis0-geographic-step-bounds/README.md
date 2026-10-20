# Geographic-step and antenna-observation bounds

**72/72 identities passed** in 13.94 seconds. Charged calls: 4,680 C steps, 72 C++ tangents and 6,624 independent references. All inputs are generated; no archive reads, full-record sweeps or optimizer starts.

| Candidate | Passed | Maximum C++ Jacobian discrepancy | Largest resolved remainder / bound |
|---|---:|---:|---:|
| sphere_rotating | 24/24 | 2.84e-14 m / normalized parameter | 0.999974 |
| sphere_still | 24/24 | 2.84e-14 m / normalized parameter | 0.999974 |
| flat_still | 24/24 | 2.16e-14 m / normalized parameter | 0.999974 |

All 27 columns remain present. Timing is either fixed at the endpoint or varies strictly inside one packet. Intervals crossing packet boundaries, repeated-step usefulness, long-record arithmetic and observational error assessment remain unqualified. Roundoff-limited comparisons are retained separately; the displayed remainder ratio excludes bounds below the declared comparison tolerance.

[Proof and frozen limits](PLAN.md) · [Local-step controls](../ilvis0-local-step-bounds/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
