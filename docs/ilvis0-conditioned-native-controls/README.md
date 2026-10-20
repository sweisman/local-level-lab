# Propagation with training-derived acceleration bounds

6/6 source-qualified native controls passed.

These are generated controls, not aircraft results. They check whether a tighter training-derived acceleration bound can be used without changing the native prediction, its derivative or shared-error coefficients.

| Candidate / removal | Source remainder N / E / height (m) | Conditioned remainder N / E / height (m) | Passed |
|---|---|---|---|
| Globe with specified field / zero | 0.198372 / 0.264139 / 0.19329 | 0.171107 / 0.227968 / 0.173645 | Yes |
| Globe with specified field / profiled | 0.217333 / 0.280201 / 0.212271 | 0.19008 / 0.244045 / 0.192634 | Yes |
| Globe with zero field / zero | 0.137269 / 0.154917 / 0.128039 | 0.116459 / 0.125147 / 0.114864 | Yes |
| Globe with zero field / profiled | 0.171214 / 0.191585 / 0.162015 | 0.150419 / 0.161838 / 0.148849 | Yes |
| Flat disc / zero | 0.0800826 / 0.0287313 / 0.0797561 | 0.0770756 / 0.0266839 / 0.0767491 | Yes |
| Flat disc / profiled | 0.119667 / 0.0412026 / 0.119337 | 0.116663 / 0.039157 / 0.116332 | Yes |

Completed in 94.1 seconds. Native calls: 12/12; enclosure calls: 6/6; exact verifier supports: 36/36. Zero LP proposals, original reads or observed fits.

A conditioned bound applies only to its verified training region. Original Taylor remainder allowances remain. This component check does not yet qualify complete prediction widths or observational coverage.

[Frozen scope](PLAN.md) · [Acceleration bounds](../ilvis0-acceleration-projection/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
