# Complete prediction covers from saved bounds

48/48 scheduled region calculations passed. The complete-cover width target passed.

| Candidate / removal | Fresh cover | Final cover | Widths north / east / height (m) | Original target |
|---|---|---|---:|---|
| Globe with specified field / zero | 8/8 | complete-intersection | 0.9558 / 1.3816 / 0.7675 | Pass |
| Globe with specified field / profiled | 8/8 | complete-intersection | 0.9872 / 1.3923 / 0.8008 | Pass |
| Globe with zero field / zero | 8/8 | complete-intersection | 0.7666 / 0.7998 / 0.5658 | Pass |
| Globe with zero field / profiled | 8/8 | complete-intersection | 0.8485 / 0.8800 / 0.6451 | Pass |
| Flat disc / zero | 8/8 | complete-intersection | 0.6459 / 0.2002 / 0.3924 | Pass |
| Flat disc / profiled | 8/8 | complete-intersection | 0.7440 / 0.2370 / 0.4865 | Pass |

Elapsed 258.34 seconds; 336/336 saved-report merges, zero integrations, zero packet propagation, zero original-aircraft reads and zero optimizer starts.

All six cases require all eight fresh regions. The serial source supplies only the twelve missing future queries; completed training reports are reused. No partial new union can qualify the matrix. Both earlier source studies retain their failed qualification labels.

This checks the existing generated 7.2-second examples, with unchanged physical bounds, observation allowance and arithmetic assumptions. Recording-scale qualification and the observation-error model remain unfinished. It adds no empirical model preferences or calibrated confidence.

[Frozen scope](PLAN.md) · [Adapter checks](../ilvis0-reused-three-controls/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
