# How the observed Doppler paths change the shape score

On one ESA development interval, substituting the GPS Doppler path
for the recorded position path shifts the frozen shape score by
**31.52% of the certified gap** between the two zero-field candidate
forecasts. The GLONASS path shifts it by **25.81%**. The difference
between the two Doppler paths contributes **5.71%** of the same gap.

| Signed path difference | Score shift as share of the gap | Largest later difference in north / east / height coordinates (m) |
| --- | ---: | ---: |
| GPS Doppler minus position solution | +31.52% | 1.45 / 0.80 / 2.03 |
| GLONASS Doppler minus position solution | +25.81% | 0.91 / 0.85 / 0.56 |
| GPS Doppler minus GLONASS Doppler | +5.71% | 0.58 / 1.51 / 2.58 |

The two Doppler paths share the first position and integrate velocity
through all 520 report times. The training cut does not reset either
path. The earlier [Doppler check](ESA_DOPPLER_COMPARISON_RESULT.md) used
a fresh anchor at that cut when reporting later displacement error.
Here, each displacement difference contributes to the fixed score
through both the 400 earlier and the 120 later reports. The forecasts,
their fitted parameters and the score weights stay fixed.

The similar signed shifts show why comparing the two Doppler paths
alone misses part of their difference from the position solution.
These are three reconstructions from one aircraft antenna, with
a common starting position. They constrain the score's sensitivity
to these particular displacement patterns. They provide no upper
bound on error shared by all three or coverage on another flight.

Seven software checks passed. The task used four bounded operations on
one thread. No fit was rerun and no reserved flight was opened.

[Frozen plan](ESA_DOPPLER_CONTRAST_PLAN.md) ·
[Signed intervals and completion record](esa-doppler-contrast-result.json)
