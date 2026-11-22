# Where the later ESA forecast error grew

The two 120-report windows on development recording 187 had very
different patterns of error. The earlier window's scores were used to
set three working covariance estimates. The same estimates then
scored the later window.

| Covariance estimated from the earlier window | Later squared score relative to the earlier score |
|---|---:|
| One common scale | 4.06× |
| A separate scale for each score channel | 17.50× |
| All three scales and their cross-channel correlations | 21.11× |

The two IMU error descriptions agree to the displayed precision.
Allowing more directional detail in the earlier covariance worsened
the transfer. The later east-ordered innovations had a lag-one
correlation of 0.955 even after applying the archived temporal error
model. A stable scale and a stable three-channel covariance both
leave a time-dependent error to explain.

| Block in the later forecast | Change in ground course | Share of east-ordered score | Share of east position error squared |
|---|---:|---:|---:|
| Reports 1–30 | +0.71° | 0.7% | 0.03% |
| Reports 31–60 | −12.94° | 2.7% | 0.51% |
| Reports 61–90 | +0.71° | 85.5% | 2.11% |
| Reports 91–120 | +0.72° | 11.1% | 97.4% |

The largest increase followed the turn. The turn block also had the
largest recorded angular-rate RMS, about 2.44°/s. The receiver continued
to report 18 satellites, a dilution-of-precision figure of about 1.25
and roughly 2 cm of east position precision. The three largest
east-ordered innovations accounted for only 15.4% of that channel's
score, so the increase spans multiple reports.

The timing suggests a concrete test of a motion-dependent error law
with a persistent response after a turn. The two windows cannot show
whether the turn caused the error or separate inertial error from
receiver error. Repeated turns and straight-flight controls are needed
to establish a rule before it is used on an independent flight.

Both replays used the original fits, factors and measured intervals.
No new fits or reserved-flight reads were needed.

[Score transfer plan](ESA_INNOVATION_TRANSFER_PLAN.md) ·
[Motion context plan](ESA_FORECAST_MOTION_PLAN.md) ·
[Earlier estimates](esa-innovation-transfer-earlier.json) ·
[Transfer results](esa-innovation-transfer-result.json) ·
[All eight motion blocks](esa-forecast-motion-result.json)
