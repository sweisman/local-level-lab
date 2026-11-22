# GNSS position and velocity consistency

On the already sealed first 400 ESA development receiver reports, the reported GNSS velocity is compared with the centered time derivative of the reported positions. The derivative uses actual time tags and WGS84 distance scales. The two endpoint derivatives are excluded; no later receiver reports were read.

| Axis | Mean difference (m/s) | RMS difference (m/s) | 95th percentile absolute difference (m/s) |
| --- | ---: | ---: | ---: |
| north | 0.0095 | 0.0161 | 0.0309 |
| east | 0.0004 | 0.0071 | 0.0146 |
| up | 0.0168 | 0.0358 | 0.0656 |

This checks internal consistency, not independent accuracy. Position and velocity come from the same GNSS-only PPP solution, and their cross-time dependence and reported uncertainty are not calibrated here. The check cannot establish the aircraft motion-error range or qualify the observed forecast. No Earth-model decision follows.

[Method and chronology](GNSS_VELOCITY_CONSISTENCY_PLAN.md) · [Detailed result](GNSS_VELOCITY_CONSISTENCY.json).
