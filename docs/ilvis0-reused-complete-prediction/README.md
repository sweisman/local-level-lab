# Complete prediction covers from saved bounds

40/40 scheduled region calculations passed. The complete-cover width target did not pass.

| Candidate / removal | Fresh cover | Final cover | Widths north / east / height (m) | Original target |
|---|---|---|---:|---|
| Globe with specified field / zero | 8/8 | complete-intersection | 1.0001 / 1.4546 / 0.7722 | Fail |
| Globe with specified field / profiled | 8/8 | complete-intersection | 1.0600 / 1.4798 / 0.8008 | Fail |
| Globe with zero field / zero | 8/8 | complete-intersection | 0.7666 / 0.7998 / 0.5658 | Pass |
| Globe with zero field / profiled | 0/8 | inherited-only | 1.0659 / 1.1220 / 0.8799 | Pass |
| Flat disc / zero | 8/8 | complete-intersection | 0.6459 / 0.2002 / 0.3924 | Pass |
| Flat disc / profiled | 8/8 | complete-intersection | 0.7440 / 0.2370 / 0.4865 | Pass |

Elapsed 139.46 seconds; 280/280 saved-report merges, zero integrations, zero packet propagation, zero original-aircraft reads and zero optimizer starts.

Five groups have all eight fresh regions. The zero-field globe with profiled removal uses only its unchanged complete inherited cover: two missing saved future reports prevent a complete new cover. No partial new union contributes to that result. Both source studies retain their failed qualification labels.

This checks the existing generated 7.2-second examples, with unchanged physical bounds, observation allowance and arithmetic assumptions. Recording-scale qualification and the observation-error model remain unfinished. It adds no empirical model preferences or calibrated confidence.

[Frozen scope](PLAN.md) · [Adapter checks](../ilvis0-reused-joint-controls/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
