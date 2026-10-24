# Predicting the later climb after learning calibration

**24/24 generated fits pass all frozen checks.** The tested training/forecast procedure qualifies.

These are twenty-minute generated northern climbing/turning tracks, not aircraft recordings.
Earlier 800 receiver positions determine initialization, working weights, calibration and the gravity anchor.
Later 400 positions score the continuous forecast after it is saved. True initial state and calibration
are not supplied. Both starts, both removal cases and both working error policies remain in the result.

| Generating candidate | Passed | Converged | Largest later horizontal RMS | Largest later height RMS | Largest later spatial error |
|---|---:|---:|---:|---:|---:|
| Globe + field | 8/8 | 8 | 8.76312e-06 m | 2.52929e-06 m | 1.90102e-05 m |
| Globe, zero field | 8/8 | 8 | 2.47773e-06 m | 3.12304e-06 m | 6.50098e-06 m |
| Tested disc | 8/8 | 8 | 3.56241e-06 m | 2.47948e-06 m | 7.31395e-06 m |

Each section requires horizontal and height RMS ≤0.1 m and maximum spatial error ≤0.5 m, plus
numerical convergence and all declared nuisance columns. No failures are replaced by better starts.
These examples have no added random measurement noise. Their error sizes are software results,
not instrument specifications, calibrated uncertainty or evidence selecting an Earth model.

The run charges 382 native calls in 0.65 hours.
The saved-only audit checks every earlier/later boundary, training-derived gravity anchor,
input-hash consistency across starts and policies, physical errors, calibration columns and charges.
Deterministic generated rate arrays are represented by frozen source/environment/recipe and hashes,
rather than repeated large array archives. The audit checks their saved bindings without regenerating
those arrays; exact raw regeneration is a separate reproducibility operation. Original measurements
are not involved or discarded.

This northern climbing geometry limits the qualification. Seven ESA confirmation groups remain
protected. A revised observed comparison needs its own finite freeze and unchanged accuracy checks.

[Frozen plan](PLAN.md) · [Known-correction gravity controls](../esa-gravity-controls/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md)
