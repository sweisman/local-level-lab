# Three GNSS receivers across the opened ESA flight

This [fixed eight-window comparison](FULL_PARALLEL_GNSS_V2_PLAN.md) extends
the earlier 400-training-epoch receiver check across the already opened ESA
development recording. It matched each other GNSS-only PPP export to `air1`
within 2 ms and removed the small position shift expected from the reported
time offset and velocity. No inertial measurements, Earth-model fits or
reserved ESA groups were used. The complete [machine result](full-parallel-gnss-v2-result.json)
contains source hashes, match counts, both raw and adjusted differences, and
their temporal correlations.

| Fixed flight window | Median ground speed | `mosaic03` matched | `mosaic03` adjusted RMS N/E/U | `pwrpak7` matched | `pwrpak7` adjusted RMS N/E/U |
|---|---:|---:|---:|---:|---:|
| 1 | 0 km/h | 3,723 | 0.009 / 0.012 / 0.022 m | 4,005 | 0.008 / 0.016 / 0.026 m |
| 2 | 336 km/h | 4,005 | 0.013 / 0.019 / 0.048 m | 4,005 | 0.007 / 0.009 / 0.049 m |
| 3 | 310 km/h | 4,005 | 0.007 / 0.021 / 0.039 m | 4,005 | 0.008 / 0.016 / 0.046 m |
| 4 | 303 km/h | 4,005 | 0.019 / 0.007 / 0.028 m | 4,005 | 0.009 / 0.008 / 0.033 m |
| 5 | 290 km/h | 4,005 | 0.023 / 0.005 / 0.038 m | 4,005 | 0.011 / 0.011 / 0.051 m |
| 6 | 274 km/h | 4,005 | 0.021 / 0.007 / 0.042 m | 4,005 | 0.013 / 0.035 / 0.026 m |
| 7 | 262 km/h | 4,005 | 0.034 / 0.008 / 0.015 m | 4,005 | 0.013 / 0.048 / 0.012 m |
| 8 | 260 km/h | 4,005 | **0.280 / 0.231 / 0.339 m** | 3,713 | 0.012 / 0.042 / 0.025 m |

Each window contains 8,010 `air1` reports. The other receivers' sampling
times coincide with about half those reports; their shorter edge coverage
also reduces the first or last match count. All matched observations remain
in the statistics. The largest timestamp offsets are under 1 ms.

The last-window `mosaic03` discrepancy is persistent, not a single isolated
point: its adjusted north/east/up lag-one correlations are about
0.9998 / 0.9998 / 0.9994, with 95th-percentile absolute differences of
0.712 / 0.510 / 0.943 m. Over the same window, `pwrpak7` stays closer to
`air1`. A [receiver-speed split](PARALLEL_GNSS_MOTION_PHASE_RESULT.md)
finds about 0.10 m north RMS difference during fast flight, growing to
0.47 m at low speed. The window includes both flight and ground time;
its full-window RMS should not be described as an airborne-only error.
This establishes a receiver-specific **relative divergence** in the
opened flight. It does not identify the true position or show which processing
stream is at fault; all three receivers share an antenna and may share errors.

The first strict full-flight attempt [stopped](FULL_PARALLEL_GNSS_V1_FAILURE.md)
at a printed `mosaic03` sequence reset. The separate v2 parser verified one
`00099999` → `00000000` rollover at increasing GPS time, preserved the
original counter text, and strictly decoded all 160,134 `mosaic03` and 31,760
`pwrpak7` records. It did not sort, interpolate or alter any coordinate.
Nine focused software checks passed.

The observed last-window divergence rules out treating cross-receiver
centimetre agreement from the first training window as a flight-wide error
guarantee. A later prediction test needs a time-varying receiver-error
sensitivity and an absolute adequacy rule. Relative agreement alone cannot
qualify that rule or decide an Earth model.
