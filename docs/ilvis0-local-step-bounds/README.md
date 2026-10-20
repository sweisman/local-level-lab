# Native midpoint local-step bounds

**30/30 identities passed** in 4.68 seconds. The study charged 1,950 C local-step calls and 3,870 independent reference calls, all on generated inputs. No archive originals, full-record native sweeps or optimizer starts.

| Candidate | Passed | Largest actual remainder / bound | Largest C/reference discrepancy |
|---|---:|---:|---:|
| sphere_rotating | 10/10 | 0.999968 | 1.21e-13 |
| sphere_still | 10/10 | 0.999968 | 1.02e-13 |
| flat_still | 10/10 | 0.99997 | 6.36e-14 |

The bounds retain joint calibration, attitude, force, latitude and processing-removal effects. Rate removal changes attitude propagation while physical Coriolis stays unchanged. Inputs must themselves have valid global bounds. Geographic predictor/corrector closure, receiver timing and long-record arithmetic remain open.

[Proof and frozen limits](PLAN.md) · [Previous increment components](../ilvis0-increment-remainders/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
