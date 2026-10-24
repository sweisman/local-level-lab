# Why the ESA stopping checks fail

**24/24 fixed-point diagnostics completed and verified.**

These are probes around the already saved calibrations, not new fits.
Only the earlier 800 receiver observations and their IMU support are used.
Every original convergence label and accuracy limit stays unchanged.

| Candidate | Removal case | Working errors | Source start | Original numerical pass | Fresh repeat identical | Replayed stopping checks |
|---|---|---|---:|---|---|---|
| Globe + field | Zero | Short memory | 0 | No | Yes | relative_cost_change |
| Globe + field | Zero | Short memory | 1 | No | Yes | relative_cost_change |
| Globe + field | Zero | Persistent | 0 | Yes | Yes | All satisfied |
| Globe + field | Zero | Persistent | 1 | No | Yes | relative_cost_change |
| Globe + field | Profiled | Short memory | 0 | No | Yes | relative_cost_change |
| Globe + field | Profiled | Short memory | 1 | No | Yes | relative_cost_change |
| Globe + field | Profiled | Persistent | 0 | No | Yes | relative_cost_change |
| Globe + field | Profiled | Persistent | 1 | No | Yes | relative_cost_change |
| Globe + zero field | Zero | Short memory | 0 | Yes | Yes | All satisfied |
| Globe + zero field | Zero | Short memory | 1 | No | Yes | position_rms |
| Globe + zero field | Zero | Persistent | 0 | Yes | Yes | All satisfied |
| Globe + zero field | Zero | Persistent | 1 | Yes | Yes | All satisfied |
| Globe + zero field | Profiled | Short memory | 0 | No | Yes | position_rms |
| Globe + zero field | Profiled | Short memory | 1 | Yes | Yes | All satisfied |
| Globe + zero field | Profiled | Persistent | 0 | No | Yes | position_rms |
| Globe + zero field | Profiled | Persistent | 1 | Yes | Yes | All satisfied |
| Disc | Zero | Short memory | 0 | No | Yes | position_rms |
| Disc | Zero | Short memory | 1 | No | Yes | position_rms |
| Disc | Zero | Persistent | 0 | Yes | Yes | All satisfied |
| Disc | Zero | Persistent | 1 | No | Yes | position_rms, position_maximum |
| Disc | Profiled | Short memory | 0 | No | Yes | position_rms |
| Disc | Profiled | Short memory | 1 | No | Yes | position_rms |
| Disc | Profiled | Persistent | 0 | No | Yes | position_rms |
| Disc | Profiled | Persistent | 1 | Yes | Yes | All satisfied |

The replay column explains the fresh local check. It does not replace
the original numerical label or add an accepted model comparison.
The accompanying table also retains cost changes, position changes and
linearization differences for every source point.

Repeated native calculations and scaled bounded corrections can identify
reproducibility or local resolution problems. They do not by themselves
prove a roundoff bound, a global optimum or instrument accuracy.

The run charged 240 native sweeps in 21.90 minutes.
The saved-array audit recomputes costs, all-column stationarity, the unchanged
bounded correction and physical position differences, with no trajectory propagation.
Seven confirmation groups remain protected.

[Every source point](fixed-points.csv) · [Frozen plan](PLAN.md) · [Original comparison](../esa-observed-height-pilot/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
