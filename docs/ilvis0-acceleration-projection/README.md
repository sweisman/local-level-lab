# Can training data constrain acceleration more tightly?

6/6 cases passed exact support and containment checks. The all-group twofold reduction target passed.

This bounds one combined quantity using saved generated controls. It does not produce new position predictions or measure aircraft uncertainty.

| Candidate / removal | Original acceleration radius (m/s²) | Projected radius (m/s²) | Fraction retained | Twofold reduction |
|---|---:|---:|---:|---|
| Globe with specified field / zero | 6.6685 | 0.502018 | 7.528% | Yes |
| Globe with specified field / profiled | 6.6685 | 0.505809 | 7.585% | Yes |
| Globe with zero field / zero | 6.6685 | 0.480747 | 7.209% | Yes |
| Globe with zero field / profiled | 6.6685 | 0.488196 | 7.321% | Yes |
| Flat disc / zero | 6.6685 | 0.467205 | 7.006% | Yes |
| Flat disc / profiled | 6.6685 | 0.476504 | 7.146% | Yes |

Completed in 2.9 seconds. Reserved 36/36 LP proposals and 108/108 exact support evaluations. Zero native integration, bounds, original-file reads or observed fits.

All 51 coordinates remain. Bounds were saved before the separate known-anchor file was opened for checking. These are necessary-region bounds; observational coverage and the complete prediction method remain unqualified.

[Frozen scope](PLAN.md) · [Previous diagnosis](../ilvis0-error-block-ablation/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
