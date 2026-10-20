# Do the extreme matrices preserve a rotation?

6/6 physical anchors pass; 36/36 extreme examples are flagged.

The test removes proposed gains and checks a rotation invariant using exact arithmetic. Its dimensionless 1e-8 numerical allowance is not a sensor specification.

| Model / removal | Anchor passes | Flagged / 6 | Largest Gram defect norm |
|---|---|---:|---:|
| Globe with specified field / zero | Yes | 6 | 0.873512 |
| Globe with specified field / profiled | Yes | 6 | 0.735333 |
| Globe with zero field / zero | Yes | 6 | 0.737675 |
| Globe with zero field / profiled | Yes | 6 | 0.83194 |
| Flat disc / zero | Yes | 6 | 0.815002 |
| Flat disc / profiled | Yes | 6 | 0.846205 |

A flag diagnoses an extreme combination admitted by the relaxed prediction method. Passing does not establish full physical realizability, correct orientation or trajectory fit. This diagnostic changes no prediction interval or aircraft result.

Completed 42/42 matrix checks in 0.6 seconds. Zero new LP proposals, native integration, bounds or original aircraft reads.

[Frozen scope](PLAN.md) · [Width diagnosis](../ilvis0-relaxed-width-audit/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
