# Complete calibration-map qualification

24/24 source/domain identities passed.

| Domain | Passing identities | Probes checked |
|---|---:|---:|
| full | 6/6 | 384 |
| sector | 6/6 | 384 |
| fixed | 6/6 | 6 |
| gain-boundary | 6/6 | 384 |

Elapsed 20.6 seconds. Reconciled 24/24 setups, 48/48 interval maps, 1158/1,158 source oracles, 1158/1,158 analytic Jacobians and 1,611,936/1,611,936 scalar inequalities.

The map retains every physical and common-error coordinate. Its source values, all 27 derivatives per component and exported relationships are checked separately. Rotation value/derivative tails are analytic; sampled agreement does not supply those bounds. Fixed domains test the original zero-radius conventions without inventing normalization denominators.

The declared normalized value allowance is 3e-10; analytic derivative comparison tolerance is 3e-8. These are numerical quantities, not IMU accuracy. Passing does not certify every floating-point operation or actual measurement coverage. Complete prediction usefulness remains a separate gate.

No LP, native prediction, original-aircraft read or observed fit ran. All probes, failures, source reports, interval outputs and work reservations are preserved.

[Frozen scope](PLAN.md) · [Why this is needed](../ilvis0-calibration-map-diagnostic/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
