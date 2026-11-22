# The two carrier bands reproduce the same Reykjavík disagreement

The two separate carrier paths agree within **1.1 cm RMS per axis**.
Each still differs by about **0.85 m vertically RMS** from the
aircraft's original GPS path. Combining the two bands changes little.

| Carrier path compared with the aircraft GPS path | North RMS | East RMS | Up RMS |
| --- | ---: | ---: | ---: |
| Dual-frequency combination | 0.273 m | 0.404 m | 0.854 m |
| L1 only | 0.278 m | 0.409 m | 0.854 m |
| L2 only | 0.282 m | 0.412 m | 0.855 m |
| L1 path compared with L2 path | 0.007 m | 0.006 m | 0.010 m |

All comparisons use the same ten satellites, 60 later timestamps,
first position and satellite geometry. This rules out the combination
of the two carrier bands as the main source of the large disagreement.
The two bands share receivers, an antenna at each location and the same
geometry. Agreement between them cannot identify which path is accurate.

The aircraft file supplies a clock offset at each epoch and omits the
header field that should say whether it was applied. The station file
explicitly records zero for that header field. The next check will
compare the original processing with a consistent correction of the
aircraft clock. [RINEX 3.04, sections 3.3 and 6.9](https://files.igs.org/pub/data/format/rinex304.pdf)

The frozen task used 60 linear solves and 600 checks on satellite
geometry, plus its input check. Four software checks passed. All 12
frozen input hashes and the completed result verified locally. No additional
source observations, inertial fits or reserved flights were used.
[Frozen plan](ESA_FIXED_REFERENCE_BAND_PLAN.md) ·
[Derived results](esa-fixed-reference-band-result.json)
