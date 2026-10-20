# Prediction with training-conditioned acceleration

48/48 cases pass correctness.

Every group meets the unchanged twofold prediction-width target: **no**.

| Candidate / removal | Complete | Width N / E / height (m) | Fraction of previous width | Twofold target |
|---|---|---:|---:|---|
| Globe with specified field / zero | Yes | 1.1964 / 1.5584 / 1.0339 | 0.9570 / 0.9595 / 0.9634 | No |
| Globe with specified field / profiled | Yes | 1.2818 / 1.6334 / 1.1203 | 0.9597 / 0.9613 / 0.9661 | No |
| Globe with zero field / zero | Yes | 0.9107 / 0.9761 / 0.7291 | 0.9571 / 0.9485 / 0.9651 | Yes |
| Globe with zero field / profiled | Yes | 1.0659 / 1.1221 / 0.8852 | 0.9631 / 0.9549 / 0.9711 | Yes |
| Flat disc / zero | Yes | 0.6692 / 0.2096 / 0.5155 | 0.9913 / 0.9840 / 0.9885 | Yes |
| Flat disc / profiled | Yes | 0.8588 / 0.2688 / 0.6987 | 0.9932 / 0.9864 / 0.9915 | Yes |

Elapsed 794.3 seconds; 48/48 enclosure calls. Zero new native predictions, original reads or observed fits. The comparison retains every source-bound coefficient, all 51 coordinates and the original training regions. Saved outcomes are checked only after prediction. These are generated software controls, not measured aircraft errors or calibrated intervals.

[Frozen scope](PLAN.md) · [Native qualification](../ilvis0-conditioned-native-controls/INTERPRETATION.md) · [Previous widths](../ilvis0-column-orientation-prediction/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
