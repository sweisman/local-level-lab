# What keeps the prediction ranges wide?

This report displays the terms of already-verified certificates. It performs no new support calculation, propagation bound or native prediction.

The table uses the predeclared known-feasible generated sector in each group. It separates the affine calibration range from the saved unshared/arithmetic allowances. Outward endpoint rounding is retained in the CSV.

| Candidate / removal | Axis | Total width (m) | Affine part (m) | Saved remainder floor (m) | Fixed target (m) | Floor exceeds target |
|---|---|---:|---:|---:|---:|---|
| Globe with specified field / zero | north | 1.0501 | 0.7079 | 0.3422 | 1.2567 | No |
| Globe with specified field / zero | east | 1.4143 | 0.9584 | 0.4560 | 1.4066 | No |
| Globe with specified field / zero | height | 1.0334 | 0.6861 | 0.3473 | 0.9204 | No |
| Globe with specified field / profiled | north | 1.1351 | 0.7549 | 0.3802 | 1.2997 | No |
| Globe with specified field / profiled | east | 1.4889 | 1.0008 | 0.4881 | 1.4443 | No |
| Globe with specified field / profiled | height | 1.1194 | 0.7342 | 0.3853 | 0.9633 | No |
| Globe with zero field / zero | north | 0.7631 | 0.5302 | 0.2329 | 1.1285 | No |
| Globe with zero field / zero | east | 0.8551 | 0.6048 | 0.2503 | 1.1557 | No |
| Globe with zero field / zero | height | 0.7286 | 0.4989 | 0.2297 | 0.8079 | No |
| Globe with zero field / profiled | north | 0.9190 | 0.6182 | 0.3009 | 1.2069 | No |
| Globe with zero field / profiled | east | 1.0246 | 0.7009 | 0.3237 | 1.2357 | No |
| Globe with zero field / profiled | height | 0.8847 | 0.5870 | 0.2977 | 0.8864 | No |
| Flat disc / zero | north | 0.5197 | 0.3655 | 0.1542 | 1.0117 | No |
| Flat disc / zero | east | 0.1883 | 0.1349 | 0.0534 | 0.3079 | No |
| Flat disc / zero | height | 0.5150 | 0.3614 | 0.1535 | 0.7648 | No |
| Flat disc / profiled | north | 0.7033 | 0.4699 | 0.2333 | 1.1033 | No |
| Flat disc / profiled | east | 0.2467 | 0.1684 | 0.0783 | 0.3354 | No |
| Flat disc / profiled | height | 0.6982 | 0.4655 | 0.2327 | 0.8567 | No |

Saved remainder floors exceed the target on 0/18 known-feasible axes.

These saved floors do not themselves prevent the target. A bounded subdivision of the physical calibration domain is therefore a justified next test before more expensive native-bound recalculation.

These floors belong to the current error-range formula; they are not measurements of sensor noise or irreducible physical uncertainty. A floor argument requires a nonempty region, established here by each sealed known generated calibration. It does not establish that every other orientation sector is physically feasible.

[Every sector/axis](width-components.csv) · [Completed comparison](README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
