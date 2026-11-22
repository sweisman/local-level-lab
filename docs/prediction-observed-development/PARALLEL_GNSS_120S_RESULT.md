# Receiver agreement over two-minute flight windows

The [fixed 120-second audit](PARALLEL_GNSS_120S_PLAN.md) compares two GNSS-only
PPP exports with the opened ESA flight's `air1` export. It uses the same
hash-checked sources, strict parsing, 2 ms matching and velocity/time
correction as the [full-flight check](FULL_PARALLEL_GNSS_V2_RESULT.md). Every
matched pair enters one GPS-time window; **fast** is labeled from receiver
speed before examining differences. The complete [per-window result](parallel-gnss-120s-result.json)
contains all windows, including ground and transitions. Three deterministic
windowing tests pass.

Each export has 195 fast windows and 23,399 matched epochs. The table reports
95th percentiles across those windows, in north/east/up metres:

| Export against `air1` | Window RMS | End-to-start change | Largest window RMS |
|---|---:|---:|---:|
| `mosaic03` | 0.090 / 0.027 / 0.075 | 0.013 / 0.011 / 0.025 | 0.180 / 0.154 / 0.170 |
| `pwrpak7` | 0.016 / 0.049 / 0.071 | 0.011 / 0.010 / 0.024 | 0.021 / 0.052 / 0.088 |

The persistent window offsets are larger than the within-window changes.
For example, `mosaic03` differs by up to 0.18 m north RMS in a fast window,
but its 95th-percentile change across a fast window is 0.013 m north. The
larger final low-speed divergence remains in the complete output; it was not
called fast or deleted.

The relative two-minute receiver drift is much smaller than the metre-scale
misses in the saved IMU-based ESA forecasts. It cannot explain those misses
*as a difference between these PPP exports*. All three share an antenna and
processing, so a shared receiver error could still be larger. This result
does not establish absolute position accuracy, a valid aircraft error law,
independent prediction coverage or an Earth-model decision.
