# Steady drift and a turn response predict different parts of the error

A steady-acceleration correction estimated on the first half of a
straight-flight interval reduced height error in the second half from
**16.43 m to 0.16 m RMS**. The same correction increased north error
from 0.76 m to 1.49 m RMS. On the shorter forecast with a turn, the
turn-response correction reduced east error from **1.04 m to 0.48 m RMS**
in the final 30 reports. The two patterns improve different components
of the forecast error.

| Scored portion and axis | Original forecast | Location and velocity correction | Add steady acceleration | Add turn response | Add both |
| --- | ---: | ---: | ---: | ---: | ---: |
| Quiet 120-report forecast, final 30, height | 0.423 | 0.134 | 0.004 | Unidentifiable | Unidentifiable |
| Turning 120-report forecast, final 30, east | 1.040 | 0.957 | 0.565 | 0.483 | 0.488 |
| Straight 400-report forecast, final 200, height | 16.425 | 6.290 | 0.157 | — | — |
| Straight 400-report forecast, final 200, north | 0.765 | 1.303 | 1.491 | — | — |

Entries are RMS position errors in metres. The first 90 reports set the
correction for each short forecast. The first 200 set the correction for
the straight forecast. The incremental and point-rate descriptions of
the two short forecasts agree to the precision shown. The quiet short
forecast provides no estimate of the maneuver coefficient. The plan
tested only state and steady-acceleration corrections on the long
straight forecast.

The estimated steady vertical acceleration differs in sign between the
quiet short and straight long forecasts. One fixed vertical acceleration
correction would therefore be a poor description even on this flight. The turn
response accounts for more east error than the steady term after the
single recorded turn. Adding both to that east estimate does slightly
worse than using the turn response alone.

The replay finished all 18 linear solves, with four rank deficiencies
in the two descriptions of the quiet forecast. It changed no original
trajectory fit. This is a same-flight test in which the correction uses
a prefix of the already scored archive. It supports testing separate
directional drift and maneuver terms. It provides neither an
independently measured accelerometer bias nor an absolute prediction
uncertainty. The next qualification needs varied drift signs and repeat
maneuvers under a rule set before scoring their later positions.

[Plan and reproduction](ESA_ERROR_SHAPE_TRANSFER_PLAN.md) ·
[Frozen inputs](esa-error-shape-transfer-freeze.json) ·
[Detailed results](esa-error-shape-transfer-result.json)
