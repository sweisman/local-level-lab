# The withheld prediction passes its position limits on all twelve receiver paths

On ESA development flight 187, the globe with the specified background field
had the lowest unadjusted 3D position error on all twelve receiver paths and
under both complete settings. It passed the original position-accuracy screen
in **24 of 24** comparisons. The forecasts and the 120 later times were fixed.

| Forecast | Unadjusted 3D RMS position error across the 24 comparisons | Passes |
| --- | ---: | ---: |
| Globe, specified background field | 4.96–8.12 m | 24/24 |
| Globe, zero background field | 2,589–2,593 m | 0/24 |
| Disc, zero background field | 3,997–4,001 m | 0/24 |

| Receiver paths | Preferred forecast horizontal RMS | Preferred forecast height RMS | Smallest additional path shift that could reach a position limit |
| --- | ---: | ---: | ---: |
| Original processed receiver and four carrier paths | 4.95–5.18 m | 0.25–1.10 m | 3.93 m RMS |
| Seven code-only stress paths | 4.72–7.75 m | 1.53–5.29 m | 2.25 m RMS |

The four limits were 10 m horizontal RMS, 30 m height RMS, 50 m peak
horizontal error and 150 m peak height error. The last column gives the
smallest arbitrary 3D RMS shift in the fixed local error coordinates that
could reach any limit. A shift can be concentrated at one report. These
numbers describe sensitivity to receiver error in the position screen.

This comparison uses metre errors before any smooth adjustment. The
separate [profiled shape check](ESA_SHAPE_RECEIVER_REPLAY_RESULT.md)
allows smooth motion corrections and brings some receiver choices closer
to a tie. All twelve receiver paths share an aircraft antenna. The
comparison supplies evidence about receiver-processing sensitivity on one
flight. Common receiver error, calibration freedom and coverage on other
flights remain open.

All twelve tasks completed, with 72 forecast evaluations and no new fits.
The original receiver scores and screen decisions reproduced. Eight
focused tests passed.

[Frozen plan](ESA_RECEIVER_ACCURACY_REPLAY_PLAN.md) ·
[All model and accuracy scores](esa-receiver-accuracy-replay-result.json) ·
[Execution receipts](esa-receiver-accuracy-replay-evidence/README.md) ·
[Reproduction bundle](esa-receiver-accuracy-replay-evidence/bundle.zip)
