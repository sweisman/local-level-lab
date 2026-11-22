# Earlier motion has little effect on the missed ESA forecasts

Carrying the archived motion state into the forecast leaves the same six
of eight windows inside the error reference under both input conventions.
The forecast that was too uncertain on the turn is unchanged. The steady
forecast still shows too much error for the model to account for.

| Window with earlier motion | Seconds since last active interval | Motion weight at the cut | Joint error score, reset → carried |
| --- | ---: | ---: | ---: |
| 21856, steady | 79 | 0.00321 | 491.84 → 487.80 |
| 22936, turn | 17 | 0.02076 | 419.01 → 404.22 |
| 41116, turn | 206 | <0.000001 | 403.08 → 403.08 |

The steady window needs to score at or below 437.69 to meet the original
reference. Under the fixed 15-second decay, its earlier motion has mostly
dissipated by the forecast cut. The other five windows had no earlier
above-threshold motion, so their scores are unchanged. The table shows the
point input, and the increment input gives the same results at this precision.

The check used the original 400 earlier report times and sealed inertial
increments for each window. It replayed all 16 original scores and changed
only the initial motion weight. Four of four tasks completed in 6.7 seconds
with 40 charged calls and zero fits. This test leaves the ESA error model
unqualified. The independent flight groups remain reserved.

- [Frozen method](ESA_PERSISTENCE_HISTORY_PLAN.md)
- [Motion weights and scores for every window](esa-persistence-history-result.json)
- [Verified evidence](esa-persistence-history-evidence/README.md)
