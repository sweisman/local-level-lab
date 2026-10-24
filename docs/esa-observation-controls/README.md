# Antenna and calibration calculation checks

**24/24 generated cases passed.**

These controls add known sensor bias/gain errors, antenna displacement,
starting-state errors, gravity offsets and latency to the earlier
independent twenty-minute maneuvering trajectories. The existing forecast
receives the exact correction vector and retains all 27 nuisance columns.

**The corrections are supplied, not estimated.** Passing checks their
application; it does not show that real observations can determine them.
No ESA recording is read and no Earth-model decision is made.

| Generating geometry | Passed | Largest horizontal RMS | Largest height RMS | Largest spatial error |
|---|---:|---:|---:|---:|
| Globe with specified field | 8/8 | 0.0299476 m | 0.0281338 m | 0.0901034 m |
| Globe with zero field | 8/8 | 0.0297033 m | 0.0274597 m | 0.0884021 m |
| Tested disc | 8/8 | 0.0335571 m | 0.0274345 m | 0.0971902 m |

The unchanged screen requires horizontal and height RMS at most 1 m
and maximum spatial error at most 5 m. Separate checks compare value
and derivative predictions and one mixed calibration direction.
Zero sensor/state-correction errors are preserved as diagnostics.
All use the declared linear-point sampling hypothesis.

The run used 96 native calls in 10.61 minutes.
Saved-only verification checks artifact hashes, complete error series,
comparison labels, compiled sources and construction journals. The main
journal distinguishes one derivative and three value calls per full case.
Publication performs no propagation or new fitting.

Training-only initialization and estimation of unknown calibration remain
open, as do receiver-error assessment, actual sampling behavior and revised
selection. The original zero-eligible inventory and all reserved confirmation
groups remain unchanged.

[Frozen plan](PLAN.md) · [Earlier geographic checks](../esa-geographic-rate-controls/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md)
