# Two start times in one ESA development flight

The new 200/120 fit and receiver-conditioning studies each finished **2/2
tasks, all passing**. Their workers used only the first 200 receiver positions
and predicted the next 120. The scoring positions were read only after both
studies closed. No reserved flight was opened.

| Training / future reports | Raw horizontal RMS | Conditioned horizontal RMS | Conditioned height RMS |
|---|---:|---:|---:|
| 200 / 120, new earlier origin | 0.352 m | 0.467 m | 0.240 m |
| 400 / 120, previously completed origin | 5.380 m | 0.561 m | 0.169 m |

Both fixed IMU error laws give nearly identical numbers at each origin. At the
new origin, receiver conditioning slightly worsens horizontal RMS. At the
older origin, it greatly improves it. This is evidence that the correction's
effect depends on the start time, even though both final 120-second forecasts
are below one metre horizontally on this flight.

All 120 new reports fall inside each axis's nominal 95% marginal range.
Their normalized errors are highly correlated across adjacent seconds
(lag-one correlation 0.928–0.999). The count **120/120 is not 120 independent
coverage trials**. The ranges also depend on an unverified aircraft error
law and fitted calibration. These same-flight outcomes do not establish 95%
coverage on a new flight, physical adequacy of every model, or a statistically
significant Earth-model decision.

This closes the question of whether the shorter forecast only works at the
previous start time: it also works at this fixed earlier origin. The next
method gate is a motion- and drift-aware error range tested on independent
generated controls, then frozen before any reserved ESA flight is scored.
More overlapping start times in recording 187 would add little independent
evidence.

[New raw result](ROLLING_ORIGIN_200_RAW_RESULT.md) ·
[New conditioned result](ROLLING_ORIGIN_200_CONDITIONAL_RESULT.md) ·
[Earlier 400/120 result](ROLLING_ORIGIN_400_CONDITIONAL_RESULT.md) ·
[Fixed plan](ROLLING_ORIGIN_200_PLAN.md) ·
[Fit evidence](rolling-origin-200-fit-runtime/README.md) ·
[Conditioning evidence](rolling-origin-200-conditioning-runtime/README.md).
