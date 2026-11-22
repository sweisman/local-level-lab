# When turn-related forecast uncertainty helps

The turn allowance improved forecasts' uncertainty scores in all four
turning windows. Applying the same turn timing to four steady-course
windows worsened every score. The steady-flight allowance improved every
steady-course score. These changes affect the predicted spread of the
errors. The predicted flight paths are the same in every scoring case.

All 16 training fits passed. The lowest training cost selected one forecast
under each of two inertial error descriptions for each steady-course window.
The eight selected forecasts were sealed before the 120 later GPS positions
per window were read. Three-dimensional RMS position errors were
**0.17–0.73 m**. The two inertial error descriptions give the same results
to the precision shown below and share the same underlying measurements.

| First GPS report in the steady window | Later 3D RMS (m) | Score gain from steady allowance | Score loss from assigning a turn to steady flight | Score loss with steady allowance already included |
| ---: | ---: | ---: | ---: | ---: |
| 21856 | 0.728 | 302.30 | 6.33 | 6.07 |
| 32716 | 0.238 | 4.07 | 12.28 | 12.23 |
| 36436 | 0.173 | 5.48 | 13.85 | 13.84 |
| 39916 | 0.332 | 49.60 | 18.61 | 18.53 |

The score rewards assigning probability to the measured positions and
penalizes unnecessarily wide uncertainty. The measured angular motion
never reached the turn threshold in the steady windows, so the turn
allowance was zero there. The [timing control](ESA_STRAIGHT_CONTROL_TIMING_CHECK.md)
then assigned each steady window the angular exposure from its matched
turn. This kept the predicted positions, GPS query times and other
uncertainty components fixed. The score loss shows that the timing of the
allowance mattered on this flight.

With the steady allowance, the mean squared standardized errors ranged
from 0.094 to 0.622 across the four windows. A correctly scaled covariance
would give an expected value of one over repeated realizations. These
four windows share ESA development recording 187, and the scale still
needs to be tested across flights. The seven separately reserved flight
groups stayed closed.

The [frozen release steps](ESA_STRAIGHT_CONTROL_RELEASE_PLAN.md) reproduce
the scoring under manifest SHA-256
`5e0bbc88c422cf92a1962017b79603bb84e28e9a105c48fa8a9f090bb75685ca`.
The [release receipt](esa-straight-control-evidence/receiver-release.json)
and [score receipt](esa-straight-control-evidence/receiver-scores.json)
record the selected forecasts and every matched result.
